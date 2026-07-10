"""
DuckDB-backed GeoParquet → A5 hexagonal heatmap endpoint.

For each bbox+zoom request:
  1. DuckDB queries points from the GeoParquet within a buffered bbox.
  2. bims/utils/a5_bin.js (Node.js, a5-js library) bins each point into an A5
     cell at a zoom-appropriate resolution and returns each cell's boundary and
     count as JSON.
  3. The result is returned as a GeoJSON FeatureCollection.

Tiles are disk-cached the same way as the MVT point tiles.
The management command ``generate_location_site_geoparquet`` clears the cache
automatically after writing a new parquet file.

URL pattern:  /api/location-sites/hex/?bbox=lon_min,lat_min,lon_max,lat_max&zoom=Z
"""
from __future__ import annotations

import json
import math
import os
import re
import subprocess
import threading

from django.conf import settings
from django.db import connection
from django.http import Http404, JsonResponse
from django.views import View

MIN_ZOOM = 1

# Map web-map zoom levels to A5 resolution levels.
# A5 res 0 = 12 cells (whole world); each +1 res quadruples the cell count.
ZOOM_TO_A5_RES: dict[int, int] = {
    0: 3, 1: 3, 2: 4, 3: 4, 4: 5, 5: 5,
    6: 6, 7: 6, 8: 7, 9: 7, 10: 8, 11: 8,
    12: 9, 13: 9, 14: 10, 15: 10,
}

# Geographic buffer in degrees around the query bbox, per A5 resolution.
# Large enough to capture cells whose centre sits just outside the viewport
# but whose polygon extends into it.
A5_RES_BUFFER: dict[int, float] = {
    0: 20.0, 1: 10.0, 2: 5.0, 3: 2.0, 4: 0.8,
    5: 0.4, 6: 0.2, 7: 0.08, 8: 0.04, 9: 0.02, 10: 0.01,
}

# Absolute path to the Node.js helper script.
_A5_HELPER = os.path.normpath(
    os.path.join(os.path.dirname(__file__), '..', 'utils', 'a5_bin.js')
)

# ── Thread-local DuckDB connections ─────────────────────────────────────────

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


# ── A5 binning via Node.js ──────────────────────────────────────────────────

def _a5_bin_points(points: list[list[float]], resolution: int) -> list[dict]:
    """Call a5_bin.js to bin lon/lat points into A5 cells.

    Returns a list of dicts: [{"count": N, "boundary": [[lon, lat], ...]}, ...]
    The boundary is already a closed GeoJSON ring (first == last point).
    """
    payload = json.dumps({"points": points, "resolution": resolution})
    proc = subprocess.run(
        ["node", _A5_HELPER],
        input=payload.encode(),
        capture_output=True,
        timeout=60,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"a5_bin.js: {proc.stderr.decode().strip()}")
    return json.loads(proc.stdout)


# ── Projection helpers (kept for future MVT tile endpoint) ──────────────────

_R = 6378137.0


def _latlng_to_3857(lat: float, lon: float) -> tuple[float, float]:
    x = lon * math.pi * _R / 180.0
    lat_c = max(-89.99, min(89.99, lat))
    y = math.log(math.tan(math.pi / 4 + math.radians(lat_c) / 2)) * _R
    return x, y


def _tile_to_bbox(z: int, x: int, y: int) -> tuple[float, float, float, float]:
    """Return (lon_min, lat_min, lon_max, lat_max) in EPSG:4326."""
    n = 2 ** z
    lon_min = x / n * 360.0 - 180.0
    lon_max = (x + 1) / n * 360.0 - 180.0
    lat_max = math.degrees(math.atan(math.sinh(math.pi * (1 - 2 * y / n))))
    lat_min = math.degrees(math.atan(math.sinh(math.pi * (1 - 2 * (y + 1) / n))))
    return lon_min, lat_min, lon_max, lat_max


def _tile_to_bbox_3857(z: int, x: int, y: int) -> tuple[float, float, float, float]:
    lon_min, lat_min, lon_max, lat_max = _tile_to_bbox(z, x, y)
    x_min, y_min = _latlng_to_3857(lat_min, lon_min)
    x_max, y_max = _latlng_to_3857(lat_max, lon_max)
    return x_min, y_min, x_max, y_max


# ── Cache helpers ────────────────────────────────────────────────────────────

def _cache_path(schema: str, z: int, x: int, y: int) -> str:
    return os.path.join(
        settings.MEDIA_ROOT, "tile_cache", "location_sites_hex", schema,
        str(z), str(x), f"{y}.mvt",
    )


def clear_hex_tile_cache(schema: str) -> None:
    import shutil
    cache_dir = os.path.join(
        settings.MEDIA_ROOT, "tile_cache", "location_sites_hex", schema
    )
    if os.path.isdir(cache_dir):
        shutil.rmtree(cache_dir)


# ── View ─────────────────────────────────────────────────────────────────────

class LocationSiteHexView(View):

    def get(self, request):
        bbox_str = request.GET.get("bbox", "")
        zoom_str = request.GET.get("zoom", "8")
        view_name = request.GET.get("view", "").strip()

        try:
            lon_min, lat_min, lon_max, lat_max = map(float, bbox_str.split(","))
            zoom = max(0, min(int(zoom_str), 15))
        except (ValueError, AttributeError):
            return JsonResponse({"error": "Invalid bbox or zoom"}, status=400)

        schema_name = getattr(connection, "schema_name", "public")
        parquet_path = os.path.join(
            settings.MEDIA_ROOT, "geoparquet",
            f"location_sites_{schema_name}.parquet",
        )
        if not os.path.exists(parquet_path):
            raise Http404("GeoParquet not found. Run generate_location_site_geoparquet first.")

        site_ids: list | None = None
        if view_name:
            if not re.match(r'^[A-Za-z0-9_\-]+$', view_name):
                return JsonResponse({"error": "Invalid view name."}, status=400)
            try:
                with connection.cursor() as cursor:
                    cursor.execute(f'SELECT site_id FROM "{view_name}"')
                    site_ids = [row[0] for row in cursor.fetchall()]
            except Exception:
                site_ids = []
            if not site_ids:
                return JsonResponse({"type": "FeatureCollection", "features": []})

        resolution = ZOOM_TO_A5_RES.get(zoom, 4)
        buf = A5_RES_BUFFER.get(resolution, 0.1)

        if site_ids is not None:
            placeholders = ", ".join(["?"] * len(site_ids))
            rows = _get_conn().execute(
                f"""
                SELECT ST_X(geometry) AS lon, ST_Y(geometry) AS lat
                FROM read_parquet(?)
                WHERE ST_Intersects(
                    geometry,
                    ST_MakeEnvelope(?, ?, ?, ?)
                )
                AND site_id IN ({placeholders})
                """,
                [parquet_path,
                 lon_min - buf, lat_min - buf,
                 lon_max + buf, lat_max + buf,
                 *site_ids],
            ).fetchall()
        else:
            rows = _get_conn().execute(
                """
                SELECT ST_X(geometry) AS lon, ST_Y(geometry) AS lat
                FROM read_parquet(?)
                WHERE ST_Intersects(
                    geometry,
                    ST_MakeEnvelope(?, ?, ?, ?)
                )
                """,
                [parquet_path,
                 lon_min - buf, lat_min - buf,
                 lon_max + buf, lat_max + buf],
            ).fetchall()

        if not rows:
            return JsonResponse({"type": "FeatureCollection", "features": []})

        # DuckDB returns (lon, lat); A5 expects [lon, lat] - already correct.
        points = [list(row) for row in rows]
        cells = _a5_bin_points(points, resolution)

        features = [
            {
                "type": "Feature",
                "geometry": {"type": "Polygon", "coordinates": [cell["boundary"]]},
                "properties": {"count": cell["count"]},
            }
            for cell in cells
        ]

        return JsonResponse({"type": "FeatureCollection", "features": features})
