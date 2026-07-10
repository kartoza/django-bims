"""
DuckDB-backed GeoParquet → MVT tile endpoint with disk cache.

Flow:
  1. Check MEDIA_ROOT/tile_cache/location_sites/<schema>/{z}/{x}/{y}.mvt
  2. Cache hit  → stream the file directly (no DuckDB, no encoding)
  3. Cache miss → DuckDB spatial query → mapbox-vector-tile encode → write cache → stream

Tiles are deterministic (parquet content + z/x/y), so they never expire
until the parquet itself is regenerated.  The management command
``generate_location_site_geoparquet`` clears the cache automatically after
writing a new parquet file.

URL pattern:  /api/location-sites/tiles/{z}/{x}/{y}/
"""
from __future__ import annotations

import math
import os
import threading

from django.conf import settings
from django.db import connection
from django.http import HttpResponse, Http404
from django.views import View

MVT_CONTENT_TYPE = "application/vnd.mapbox-vector-tile"

# Tiles below this zoom level return empty (too many features, unreadable anyway).
MIN_ZOOM = 5

# ── Thread-local DuckDB connections ────────────────────────────────────────

_local = threading.local()


def _get_conn():
    if not getattr(_local, "conn", None):
        import duckdb
        conn = duckdb.connect()
        try:
            conn.execute("LOAD spatial")
        except Exception:
            conn.execute("INSTALL spatial; LOAD spatial")
        _local.conn = conn
    return _local.conn


# ── Tile math ───────────────────────────────────────────────────────────────

def _tile_to_bbox(z: int, x: int, y: int) -> tuple[float, float, float, float]:
    """Return (lon_min, lat_min, lon_max, lat_max) in EPSG:4326."""
    n = 2 ** z
    lon_min = x / n * 360.0 - 180.0
    lon_max = (x + 1) / n * 360.0 - 180.0
    lat_max = math.degrees(math.atan(math.sinh(math.pi * (1 - 2 * y / n))))
    lat_min = math.degrees(math.atan(math.sinh(math.pi * (1 - 2 * (y + 1) / n))))
    return lon_min, lat_min, lon_max, lat_max


# ── Cache helpers ────────────────────────────────────────────────────────────

def _cache_path(schema: str, z: int, x: int, y: int) -> str:
    return os.path.join(
        settings.MEDIA_ROOT, "tile_cache", "location_sites", schema,
        str(z), str(x), f"{y}.mvt",
    )


def clear_tile_cache(schema: str) -> None:
    """Delete all cached MVT tiles for *schema*. Called after parquet regeneration."""
    import shutil
    cache_dir = os.path.join(
        settings.MEDIA_ROOT, "tile_cache", "location_sites", schema
    )
    if os.path.isdir(cache_dir):
        shutil.rmtree(cache_dir)


# ── View ─────────────────────────────────────────────────────────────────────

class LocationSiteTileView(View):

    def get(self, request, z: int, x: int, y: int):
        schema_name = getattr(connection, "schema_name", "public")

        # Return empty tile below minimum zoom.
        if z < MIN_ZOOM:
            return HttpResponse(b"", content_type=MVT_CONTENT_TYPE)

        # ── 1. Cache hit ────────────────────────────────────────────────────
        cache_file = _cache_path(schema_name, z, x, y)
        if os.path.exists(cache_file):
            with open(cache_file, "rb") as fh:
                return HttpResponse(fh.read(), content_type=MVT_CONTENT_TYPE)

        # ── 2. Cache miss: generate tile ────────────────────────────────────
        parquet_path = os.path.join(
            settings.MEDIA_ROOT, "geoparquet",
            f"location_sites_{schema_name}.parquet",
        )
        if not os.path.exists(parquet_path):
            raise Http404(
                "GeoParquet file not found. Run generate_location_site_geoparquet first."
            )

        lon_min, lat_min, lon_max, lat_max = _tile_to_bbox(z, x, y)

        rows = _get_conn().execute(
            """
            SELECT
                site_id,
                name,
                site_code,
                ecosystem_type,
                ST_AsText(geometry) AS geom_wkt
            FROM read_parquet(?)
            WHERE ST_Intersects(
                geometry,
                ST_MakeEnvelope(?, ?, ?, ?)
            )
            """,
            [parquet_path, lon_min, lat_min, lon_max, lat_max],
        ).fetchall()

        features = [
            {
                "geometry": row[4],
                "properties": {
                    "site_id": row[0],
                    "name": row[1] or "",
                    "site_code": row[2] or "",
                    "ecosystem_type": row[3] or "",
                },
            }
            for row in rows
        ]

        from mapbox_vector_tile import encode
        mvt = encode(
            {"name": "sites", "features": features},
            quantize_bounds=(lon_min, lat_min, lon_max, lat_max),
            extents=4096,
        )

        # ── 3. Write cache ──────────────────────────────────────────────────
        os.makedirs(os.path.dirname(cache_file), exist_ok=True)
        with open(cache_file, "wb") as fh:
            fh.write(mvt)

        return HttpResponse(mvt, content_type=MVT_CONTENT_TYPE)
