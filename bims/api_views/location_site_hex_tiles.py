"""
DuckDB-backed GeoParquet → H3 hexagonal heatmap MVT tile endpoint.

For each XYZ tile:
  1. DuckDB queries points from the GeoParquet within a buffered bbox.
  2. Python h3 bins each point into an H3 cell at a zoom-appropriate resolution.
  3. Only hexagons whose centre lies within the original tile bbox are returned.
  4. H3 boundary vertices are projected from EPSG:4326 → EPSG:3857 before MVT
     encoding, which eliminates the skew artefact caused by linear quantization
     of geographic coordinates.
  5. Returns an MVT tile — same format as the point tile endpoint.

Tiles are disk-cached the same way as the MVT point tiles.

URL pattern:  /api/location-sites/hex-tiles/{z}/{x}/{y}/
"""
from __future__ import annotations

import math
import os
import threading
from collections import Counter

from django.conf import settings
from django.db import connection
from django.http import Http404, HttpResponse
from django.views import View

MVT_CONTENT_TYPE = "application/vnd.mapbox-vector-tile"

MIN_ZOOM = 1

ZOOM_TO_H3_RES: dict[int, int] = {
    0: 0, 1: 1, 2: 1, 3: 2, 4: 3, 5: 3,
    6: 4, 7: 4, 8: 5, 9: 5, 10: 6, 11: 6,
    12: 7, 13: 7, 14: 8, 15: 8,
}

H3_RES_BUFFER: dict[int, float] = {
    0: 5.0, 1: 2.5, 2: 1.0, 3: 0.5, 4: 0.15, 5: 0.06,
    6: 0.02, 7: 0.008, 8: 0.003, 9: 0.001,
}


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


# ── Projection helpers ──────────────────────────────────────────────────────

_R = 6378137.0


def _latlng_to_3857(lat: float, lon: float) -> tuple[float, float]:
    """Project geographic coordinates to Web Mercator (EPSG:3857)."""
    x = lon * math.pi * _R / 180.0
    lat_c = max(-89.99, min(89.99, lat))
    y = math.log(math.tan(math.pi / 4 + math.radians(lat_c) / 2)) * _R
    return x, y


# ── Tile math ───────────────────────────────────────────────────────────────

def _tile_to_bbox(z: int, x: int, y: int) -> tuple[float, float, float, float]:
    """Return (lon_min, lat_min, lon_max, lat_max) in EPSG:4326."""
    n = 2 ** z
    lon_min = x / n * 360.0 - 180.0
    lon_max = (x + 1) / n * 360.0 - 180.0
    lat_max = math.degrees(math.atan(math.sinh(math.pi * (1 - 2 * y / n))))
    lat_min = math.degrees(math.atan(math.sinh(math.pi * (1 - 2 * (y + 1) / n))))
    return lon_min, lat_min, lon_max, lat_max


def _tile_to_bbox_3857(z: int, x: int, y: int) -> tuple[float, float, float, float]:
    """Return (x_min, y_min, x_max, y_max) in EPSG:3857 (metres)."""
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


# ── Single-view hex endpoint ──────────────────────────────────────────────────
#
# Returns a GeoJSON FeatureCollection covering the entire requested bbox in one
# shot.  The frontend uses ol.source.Vector (not tiled), so OL reprojects each
# vertex with proper Mercator math — no linear-quantization skew.
#
# URL:  /api/location-sites/hex/?bbox=lon_min,lat_min,lon_max,lat_max&zoom=Z

class LocationSiteHexView(View):

    def get(self, request):
        import h3
        from django.http import JsonResponse

        bbox_str = request.GET.get("bbox", "")
        zoom_str = request.GET.get("zoom", "8")

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

        resolution = ZOOM_TO_H3_RES.get(zoom, 4)
        buf = H3_RES_BUFFER.get(resolution, 0.1)

        rows = _get_conn().execute(
            """
            SELECT ST_Y(geometry) AS lat, ST_X(geometry) AS lon
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

        cell_counts: Counter = Counter()
        for lat, lon in rows:
            cell = h3.latlng_to_cell(lat, lon, resolution)
            cell_counts[cell] += 1

        features = []
        for cell, count in cell_counts.items():
            boundary = h3.cell_to_boundary(cell)  # [(lat, lon), ...]
            coords = [[lon, lat] for lat, lon in boundary]
            coords.append(coords[0])  # close ring
            features.append({
                "type": "Feature",
                "geometry": {"type": "Polygon", "coordinates": [coords]},
                "properties": {"count": count},
            })

        return JsonResponse({"type": "FeatureCollection", "features": features})
