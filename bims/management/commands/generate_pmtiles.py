"""
Management command: generate_pmtiles

Generate or regenerate a PMTiles archive for one or more *Layer* records.

Usage examples
--------------

Generate PMTiles for one layer in the current schema::

    python manage.py generate_pmtiles --layer-id 42

Generate PMTiles for several layers::

    python manage.py generate_pmtiles --layer-id 42 43 44

Run inside a specific tenant schema (requires django-tenants)::

    python manage.py generate_pmtiles --layer-id 42 --tenant acme

If no ``--layer-id`` is passed the command will *list* available layers instead
of generating anything, preventing accidental bulk generation.
"""
from __future__ import annotations

import os
import shlex
import shutil
import subprocess
import sys
import tempfile
import logging
from typing import Iterable, List

from django.conf import settings
from django.core.files.base import File
from django.core.management.base import BaseCommand
from django.db import transaction

from bims.models import LocationContext  # noqa: F401  # kept for backwards-compat import side-effects
from bims.models.location_site import LocationSite  # noqa: F401

from cloud_native_gis.models import Layer

try:
    from django_tenants.utils import get_tenant_model, schema_context
except ImportError:  # pragma: no cover
    get_tenant_model = None  # type: ignore[assignment]
    schema_context = None  # type: ignore[assignment]

logger = logging.getLogger("bims.generate_pmtiles")

PMTILES_FOLDER = getattr(settings, "PMTILES_FOLDER", "pmtiles")


def _generate_pmtiles(layer: Layer):
    """
    Generate PMTiles for *layer* using tippecanoe with flags that handle
    dense datasets (--drop-fraction-as-needed).

    Returns (bool, str) matching the cloud_native_gis Layer.generate_pmtiles()
    contract so this can be swapped in transparently.
    """
    layer_upload = layer.layerupload_set.last()
    if not layer_upload:
        msg = f"No uploads found for layer '{layer.name}'."
        logger.error(msg)
        return False, msg

    layer_files = getattr(layer_upload, "files", None) or []
    shp_file = next((f for f in layer_files if f.lower().endswith(".shp")), None)
    if not shp_file:
        msg = f"No shapefile (.shp) found for layer '{layer.name}'."
        logger.error(msg)
        return False, msg

    ogr2ogr_path = shutil.which("ogr2ogr")
    tippecanoe_path = shutil.which("tippecanoe")
    if not ogr2ogr_path or not tippecanoe_path:
        msg = "ogr2ogr or tippecanoe is not installed on the server."
        logger.error(msg)
        return False, msg

    shp_file_path = layer_upload.filepath(shp_file)
    base_name = os.path.splitext(os.path.basename(shp_file))[0]

    pmtiles_folder = os.path.join(settings.MEDIA_ROOT, PMTILES_FOLDER)
    os.makedirs(pmtiles_folder, exist_ok=True)
    pmtiles_filename = f"{base_name}.pmtiles"
    pmtiles_filepath = os.path.join(pmtiles_folder, pmtiles_filename)

    with tempfile.TemporaryDirectory() as tmpdir:
        json_filepath = os.path.join(tmpdir, f"{base_name}.geojson")

        ogr_cmd = [
            ogr2ogr_path,
            "-t_srs", "EPSG:4326",
            json_filepath,
            shp_file_path,
        ]
        logger.info("Step 1: Reproject to GeoJSON")
        logger.info("$ %s", shlex.join(ogr_cmd))
        try:
            res = subprocess.run(
                ogr_cmd, check=True,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
            )
            if res.stderr.strip():
                logger.debug("[ogr2ogr stderr]\n%s", res.stderr.strip())
        except subprocess.CalledProcessError as e:
            logs = (e.stderr or "") + (e.stdout or "")
            msg = f"ogr2ogr failed.\n{logs[:2000]}"
            logger.error(msg)
            return False, msg

        if os.path.exists(pmtiles_filepath):
            try:
                os.remove(pmtiles_filepath)
            except OSError as e:
                logger.warning("Could not remove existing PMTiles: %s", e)

        tippecanoe_cmd = [
            tippecanoe_path,
            "-zg",
            "--projection=EPSG:4326",
            "--extend-zooms-if-still-dropping",
            "--drop-fraction-as-needed",
            "--read-parallel",
            "-o", pmtiles_filepath,
            "-l", "default",
            json_filepath,
        ]
        logger.info("Step 2: Generate PMTiles")
        logger.info("$ %s", shlex.join(tippecanoe_cmd))
        try:
            res = subprocess.run(
                tippecanoe_cmd, check=True,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
            )
            if res.stderr.strip():
                logger.debug("[tippecanoe stderr]\n%s", res.stderr.strip())
        except subprocess.CalledProcessError as e:
            logs = (e.stderr or "") + (e.stdout or "")
            msg = (
                f"Failed to generate PMTiles for layer '{layer.name}'.\n"
                f"{logs[:2000]}\n\n"
                f"# Manual reproduction:\n"
                f"$ {shlex.join(ogr_cmd)}\n"
                f"$ {shlex.join(tippecanoe_cmd)}"
            )
            logger.error(msg)
            return False, msg

        try:
            size_b = os.path.getsize(pmtiles_filepath)
            logger.info(
                "PMTiles created: %s (%.2f MB)", pmtiles_filepath,
                size_b / (1024 * 1024),
            )
        except OSError:
            pass

        try:
            with open(pmtiles_filepath, "rb") as fh:
                layer.pmtile.save(pmtiles_filename, File(fh), save=True)
        except Exception as e:
            msg = (
                f"Failed attaching PMTiles to layer: {e}\n\n"
                f"# Manual reproduction:\n"
                f"$ {shlex.join(ogr_cmd)}\n"
                f"$ {shlex.join(tippecanoe_cmd)}"
            )
            logger.error(msg)
            return False, msg

    ok_msg = f"PMTiles generated successfully for layer '{layer.name}'."
    logger.info(ok_msg)
    return True, ok_msg


class Command(BaseCommand):
    """Generate (or regenerate) PMTiles archives for the given *Layer* IDs."""

    help = "Generate PMTiles archive(s) for the specified Layer ID(s)."

    def add_arguments(self, parser) -> None:
        parser.add_argument(
            "--layer-id",
            dest="layer_ids",
            nargs="+",
            type=int,
            metavar="ID",
            help="One or more Layer primary-key values to process.",
        )
        parser.add_argument(
            "--tenant",
            metavar="SCHEMA",
            help=(
                "Target schema name when using django-tenants. "
                "If omitted, the command runs in the current schema."
            ),
        )

    def handle(self, *args, **options):
        layer_ids: List[int] | None = options.get("layer_ids")
        schema: str | None = options.get("tenant")

        if schema:
            if schema_context is None:
                self.stderr.write(
                    self.style.ERROR(
                        "--tenant requires django-tenants, which is "
                        "not installed or could not be imported."
                    )
                )
                sys.exit(1)

            tenant = self._get_tenant(schema)
            if not tenant:
                sys.exit(1)

            with schema_context(tenant.schema_name):
                if layer_ids is None:
                    self._print_layers_help()
                    self.stderr.write(
                        self.style.ERROR("No --layer-id supplied. Nothing to do.")
                    )
                    sys.exit(1)

                self._run_for_layers(layer_ids, label=f"tenant '{schema}'")
        else:
            self._run_for_layers(layer_ids, label="current schema")

    def _run_for_layers(self, layer_ids: Iterable[int], label: str) -> None:
        processed = 0
        for pk in layer_ids:
            try:
                layer: Layer = Layer.objects.get(pk=pk)
            except Layer.DoesNotExist:
                self.stderr.write(self.style.ERROR(f"[{label}] Layer {pk} not found."))
                continue

            self.stdout.write(
                self.style.MIGRATE_HEADING(f"[{label}] Generating PMTiles for Layer {pk} …")
            )

            try:
                with transaction.atomic():
                    status, message = _generate_pmtiles(layer)
                    level = self.style.SUCCESS if status else self.style.ERROR
                    self.stdout.write(level(f"Layer {pk}: {status}"))
                    self.stdout.write(level(f"Layer {pk}: {message}"))
            except Exception as exc:
                self.stderr.write(
                    self.style.ERROR(f"[{label}] Failed Layer {pk}: {exc}")
                )
            else:
                if status:
                    processed += 1
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"[{label}] Layer {pk}: PMTiles generated successfully."
                        )
                    )

        if processed == 0:
            self.stderr.write(self.style.WARNING(f"[{label}] No layers processed."))
        else:
            self.stdout.write(
                self.style.SUCCESS(f"[{label}] Completed. {processed} layer(s) processed.")
            )

    def _get_tenant(self, schema_name):
        Tenant = get_tenant_model()
        try:
            return Tenant.objects.get(schema_name=schema_name)
        except Tenant.DoesNotExist:
            self.stderr.write(
                self.style.ERROR(f"Tenant with schema '{schema_name}' not found.")
            )
            return None

    def _print_layers_help(self) -> None:
        self.stdout.write(self.style.HTTP_INFO("Available layers in current schema:"))
        for layer in Layer.objects.all().only("id", "name").order_by("id"):
            self.stdout.write(f"  • {layer.id}: {layer.name}")
