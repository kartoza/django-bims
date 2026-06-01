"""
Management command: generate_location_site_geoparquet

Export LocationSite records to a GeoParquet file suitable for loading in a
map viewer (e.g. QGIS, DeckGL, Leaflet + PMTiles, etc.).

Usage
-----

Export all sites with at least one validated biological record::

    python manage.py generate_location_site_geoparquet

Export every site (including those without records)::

    python manage.py generate_location_site_geoparquet --all

Write to a custom path::

    python manage.py generate_location_site_geoparquet --output /tmp/sites.parquet

Run inside a specific tenant schema (requires django-tenants)::

    python manage.py generate_location_site_geoparquet --tenant acme
"""
from __future__ import annotations

import os
import sys

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import connection

try:
    from django_tenants.utils import get_tenant_model, schema_context
except ImportError:
    get_tenant_model = None
    schema_context = None


class Command(BaseCommand):
    help = "Export LocationSite records to a GeoParquet file."

    def add_arguments(self, parser) -> None:
        parser.add_argument(
            "--output",
            metavar="PATH",
            help=(
                "Destination file path. Defaults to "
                "<MEDIA_ROOT>/geoparquet/location_sites.parquet"
            ),
        )
        parser.add_argument(
            "--all",
            dest="all_sites",
            action="store_true",
            default=False,
            help="Include sites that have no biological records (default: validated records only).",
        )
        parser.add_argument(
            "--tenant",
            metavar="SCHEMA",
            help="Target django-tenants schema name. Runs in current schema if omitted.",
        )

    def handle(self, *args, **options) -> None:
        schema: str | None = options.get("tenant")

        if schema:
            if schema_context is None or get_tenant_model is None:
                self.stderr.write(
                    self.style.ERROR(
                        "--tenant requires django-tenants, which is not installed."
                    )
                )
                sys.exit(1)

            Tenant = get_tenant_model()
            try:
                tenant = Tenant.objects.get(schema_name=schema)
            except Tenant.DoesNotExist:
                self.stderr.write(
                    self.style.ERROR(f"Tenant with schema '{schema}' not found.")
                )
                sys.exit(1)

            with schema_context(tenant.schema_name):
                self._export(options)
        else:
            self._export(options)

    def _export(self, options: dict) -> None:
        try:
            import geopandas as gpd
            import pandas as pd
            from shapely.geometry import Point
        except ImportError as exc:
            self.stderr.write(
                self.style.ERROR(
                    f"Required library not available: {exc}. "
                    "Install geopandas (which includes shapely and pyarrow)."
                )
            )
            sys.exit(1)

        all_sites: bool = options["all_sites"]
        output_path: str | None = options.get("output")

        from bims.models.location_site import LocationSite
        from bims.models.biological_collection_record import BiologicalCollectionRecord

        qs = LocationSite.objects.select_related("location_type", "river")

        if not all_sites:
            validated_site_ids = (
                BiologicalCollectionRecord.objects
                .filter(validated=True)
                .values_list("site_id", flat=True)
                .distinct()
            )
            qs = qs.filter(id__in=validated_site_ids)

        qs = qs.filter(geometry_point__isnull=False)

        total = qs.count()
        if total == 0:
            self.stderr.write(self.style.WARNING("No sites found – nothing exported."))
            return

        self.stdout.write(f"Exporting {total} location site(s)…")

        # ------------------------------------------------------------------ #
        # Build records
        # ------------------------------------------------------------------ #
        records = []
        for site in qs.iterator(chunk_size=1000):
            pt = site.geometry_point
            records.append(
                {
                    "site_id": site.id,
                    "name": site.name or "",
                    "site_code": site.site_code or "",
                    "site_description": site.site_description or "",
                    "ecosystem_type": site.ecosystem_type or "",
                    "location_type": (
                        site.location_type.name if site.location_type_id else ""
                    ),
                    "river_name": (
                        site.river.name if site.river_id else (site.legacy_river_name or "")
                    ),
                    "latitude": site.latitude,
                    "longitude": site.longitude,
                    "geometry": Point(pt.x, pt.y),
                }
            )

        df = pd.DataFrame(records)
        gdf = gpd.GeoDataFrame(df, geometry="geometry", crs="EPSG:4326")

        try:
            import geohash2 as geohash
            gdf["_gh"] = gdf.apply(
                lambda r: geohash.encode(r.geometry.y, r.geometry.x, precision=7), axis=1
            )
            gdf = gdf.sort_values("_gh").drop(columns=["_gh"]).reset_index(drop=True)
        except ImportError:
            # geohash2 not installed – fall back to simple lat/lon sort (still helps).
            gdf = gdf.sort_values(["latitude", "longitude"]).reset_index(drop=True)

        if not output_path:
            schema_name = connection.schema_name if hasattr(connection, "schema_name") else "public"
            out_dir = os.path.join(settings.MEDIA_ROOT, "geoparquet")
            os.makedirs(out_dir, exist_ok=True)
            output_path = os.path.join(out_dir, f"location_sites_{schema_name}.parquet")

        out_dir = os.path.dirname(os.path.abspath(output_path))
        os.makedirs(out_dir, exist_ok=True)

        gdf.to_parquet(output_path, index=False, compression="snappy")

        self.stdout.write(
            self.style.SUCCESS(f"GeoParquet written to: {output_path}")
        )
        self.stdout.write(f"  CRS  : EPSG:4326")
        self.stdout.write(f"  Rows : {len(gdf)}")
        self.stdout.write(f"  Cols : {', '.join(c for c in gdf.columns if c != 'geometry')}")

        # Clear the MVT tile cache so stale tiles are not served after regeneration.
        from bims.api_views.location_site_tiles import clear_tile_cache
        from bims.api_views.location_site_hex_tiles import clear_hex_tile_cache
        schema_name = connection.schema_name if hasattr(connection, "schema_name") else "public"
        clear_tile_cache(schema_name)
        clear_hex_tile_cache(schema_name)
        self.stdout.write("  Tile cache cleared.")
