import json
import os

from django.conf import settings
from django.db import connection
from django.http import JsonResponse, Http404
from django.views import View


class LocationSiteGeoJsonView(View):
    """Serve the pre-generated GeoParquet of location sites as GeoJSON.

    The file is written by the ``generate_location_site_geoparquet`` management
    command.  It is read once per request and streamed as application/json.
    """

    def get(self, request, *args, **kwargs):
        try:
            import geopandas as gpd
        except ImportError:
            return JsonResponse(
                {"error": "geopandas is required but not installed."},
                status=500,
            )

        schema_name = getattr(connection, "schema_name", "public")
        parquet_path = os.path.join(
            settings.MEDIA_ROOT,
            "geoparquet",
            f"location_sites_{schema_name}.parquet",
        )

        if not os.path.exists(parquet_path):
            raise Http404(f"GeoParquet file not found: {parquet_path}")

        gdf = gpd.read_parquet(parquet_path)

        # Keep only the columns that the map needs; drop heavy/unused ones.
        keep = [c for c in ("site_id", "name", "site_code", "ecosystem_type", "geometry") if c in gdf.columns]
        gdf = gdf[keep]

        return JsonResponse(json.loads(gdf.to_json()), safe=False)


class SearchViewSiteIdsView(View):
    """Return the list of site_id values stored in a search materialized view.

    The view name comes from the ``view`` query parameter and corresponds to
    ``SearchProcess.process_id`` (a UUID-like string used as the DB view name).
    """

    def get(self, request, *args, **kwargs):
        view_name = request.GET.get("view", "").strip()
        if not view_name:
            return JsonResponse({"site_ids": []})

        # Validate: only allow identifier-safe characters to prevent SQL injection.
        import re
        if not re.match(r'^[A-Za-z0-9_\-]+$', view_name):
            return JsonResponse({"error": "Invalid view name."}, status=400)

        try:
            with connection.cursor() as cursor:
                cursor.execute(f'SELECT site_id FROM "{view_name}"')
                rows = cursor.fetchall()
            site_ids = [row[0] for row in rows]
        except Exception:
            # View may not exist yet (search still processing).
            site_ids = []

        return JsonResponse({"site_ids": site_ids})
