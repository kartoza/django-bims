# coding=utf-8
from django.db import connection


def get_feature_data(lon, lat, context_key: str, layer_name: str, tolerance: float = 0) -> str:
    """
    Geography-aware variant of get_feature_data.

    Uses the metre-based query_features below so it works correctly for
    linestring layers (rivers).  tolerance is in **metres**.
    """
    from cloud_native_gis.models import Layer

    layer = Layer.objects.filter(name__istartswith=layer_name).first()
    if not layer:
        layer = Layer.objects.filter(name__icontains=layer_name).first()
    if not layer:
        return ''

    features = query_features(
        table_name=layer.query_table_name,
        field_names=[context_key],
        coordinates=[(lon, lat)],
        tolerance=tolerance,
    )
    results = features.get('result', [])
    if results and 'feature' in results[0] and context_key in results[0]['feature']:
        return results[0]['feature'][context_key]
    return ''


def query_features(
        table_name: str,
        field_names: list,
        coordinates: list,
        tolerance: float,
        srid: int = 4326) -> dict:
    """
    Return raw feature data for coordinates within a radius.

    Tolerance is in **metres** (uses PostGIS geography cast so distances are
    geodetic regardless of the stored geometry type or SRID).  This makes the
    function work correctly for both polygon layers (point-in-polygon distance
    is 0 m) and linestring layers (rivers, roads, etc.).

    Args:
        table_name: PostGIS table name (schema-qualified if needed).
        field_names: Attribute columns to retrieve.
        coordinates: List of (x, y) / (lon, lat) tuples.
        tolerance: Search radius in **metres**.
        srid: SRID of the input coordinates (default 4326).
    """
    data = []
    status_message = ''

    for x, y in coordinates:
        point_wkt = f"ST_Transform(ST_SetSRID(ST_MakePoint({x}, {y}), {srid}), 4326)"

        sql = f"""
            SELECT {', '.join([f'"{f}"' for f in field_names])},
                   ST_AsGeoJSON(ST_Transform(geometry, {srid})) AS geometry
            FROM {table_name}
            WHERE ST_DWithin(
                ST_Transform(geometry, 4326)::geography,
                {point_wkt}::geography,
                {tolerance}
            )
            ORDER BY ST_Distance(
                ST_Transform(geometry, 4326)::geography,
                {point_wkt}::geography
            )
            LIMIT 1;
        """

        try:
            with connection.cursor() as cursor:
                cursor.execute(sql)
                row = cursor.fetchone()
                if row:
                    feature = {f: row[i] for i, f in enumerate(field_names)}
                    data.append({'coordinates': (x, y), 'feature': feature})
                else:
                    data.append({
                        'coordinates': (x, y),
                        'feature': {f: '' for f in field_names},
                    })
        except Exception as e:
            error_message = str(e)
            if 'does not exist' in error_message:
                parts = error_message.split('"')
                missing = parts[1] if len(parts) > 1 else error_message
                status_message = f"Column '{missing}' does not exist."
            else:
                status_message = f"An error occurred: {error_message}"
            break

    return {'status_message': status_message, 'result': data}
