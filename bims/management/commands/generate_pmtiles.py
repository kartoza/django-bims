"""
Management command: generate_pmtiles

Generate or regenerate a PMTiles archive for one or more *Layer* records. The
command delegates to :py:meth:`Layer.generate_pmtiles` and handles
multi‑tenant environments powered by **django‑tenants**.

Usage examples
--------------

Generate PMTiles for one layer in the current schema::

    python manage.py generate_pmtiles --layer-id 42

Generate PMTiles for several layers::

    python manage.py generate_pmtiles --layer-id 42 43 44

Run inside a specific tenant schema (requires django‑tenants)::

    python manage.py generate_pmtiles --layer-id 42 --tenant acme

If no ``--layer-id`` is passed the command will *list* available layers instead
of generating anything, preventing accidental bulk generation.
"""
from __future__ import annotations

import sys
from typing import Iterable, List

from django.core.management.base import BaseCommand
from django.db import transaction

from bims.models import LocationContext  # noqa: F401  # kept for backwards‑compat import side‑effects
from bims.models.location_site import LocationSite  # noqa: F401

from cloud_native_gis.models import Layer

try:
    from django_tenants.utils import get_tenant_model, schema_context
except ImportError:  # pragma: no cover
    get_tenant_model = None  # type: ignore[assignment]
    schema_context = None  # type: ignore[assignment]


class Command(BaseCommand):
    """Generate (or regenerate) PMTiles archives for the given *Layer* IDs."""

    help = "Generate PMTiles archive(s) for the specified Layer ID(s)."

    # ------------------------------------------------------------------
    # Argument parsing
    # ------------------------------------------------------------------
    def add_arguments(self, parser) -> None:
        parser.add_argument(
            "--layer-id",
            dest="layer_ids",
            nargs="+",
            type=int,
            metavar="ID",
            help="One or more Layer primary‑key values to process.",
        )
        parser.add_argument(
            "--tenant",
            metavar="SCHEMA",
            help=(
                "Target schema name when using django‑tenants. "
                "If omitted, the command runs in the current schema."
            ),
        )

    # ------------------------------------------------------------------
    # Management command entry‑point
    # ------------------------------------------------------------------
    def handle(self, *args, **options):  # noqa: D401
        layer_ids: List[int] | None = options.get("layer_ids")
        schema: str | None = options.get("tenant")

        if schema:
            if schema_context is None:
                self.stderr.write(
                    self.style.ERROR(
                        "--tenant requires django‑tenants, which is "
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

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
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
                    status, message = layer.generate_pmtiles()
                    self.stdout.write(
                        self.style.SUCCESS(f"Layer {pk}: {status}")
                    )
                    self.stdout.write(
                        self.style.SUCCESS(f"Layer {pk}: {message}")
                    )
            except Exception as exc:  # pragma: no cover
                self.stderr.write(
                    self.style.ERROR(f"[{label}] Failed Layer {pk}: {exc}")
                )
            else:
                processed += 1
                self.stdout.write(
                    self.style.SUCCESS(f"[{label}] Layer {pk}: PMTiles generated successfully.")
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
        """Print an informative table with available layers."""
        self.stdout.write(self.style.HTTP_INFO("Available layers in current schema:"))
        for layer in Layer.objects.all().only("id", "name").order_by("id"):
            self.stdout.write(f"  • {layer.id}: {layer.name}")
