import datetime
import json
import logging

logger = logging.getLogger('bims')


def parse_extent(geo_bounds: dict) -> list:
    """
    Convert an OpenSearch geo_bounds aggregation result to
    [min_lon, min_lat, max_lon, max_lat].

    Returns [] when bounds are missing or contain nulls.
    Pads single-point extents by 0.01 degrees so OL view.fit() does not fail.
    """
    bounds = geo_bounds.get('bounds', {})
    if not bounds:
        return []
    tl = bounds.get('top_left', {})   # northwest: min_lon, max_lat
    br = bounds.get('bottom_right', {})  # southeast: max_lon, min_lat
    coords = [
        tl.get('lon'),  # west  (min_lon)
        br.get('lat'),  # south (min_lat)
        br.get('lon'),  # east  (max_lon)
        tl.get('lat'),  # north (max_lat)
    ]
    if any(c is None for c in coords):
        return []
    min_lon, min_lat, max_lon, max_lat = coords
    if min_lon == max_lon and min_lat == max_lat:
        delta = 0.01
        coords = [min_lon - delta, min_lat - delta, max_lon + delta, max_lat + delta]
    return coords


def build_security_filter(user) -> list:
    today = datetime.date.today().strftime('%Y-%m-%d')
    clauses = []

    if user is None or not hasattr(user, 'is_authenticated') or not user.is_authenticated:
        clauses.append({'term': {'data_type': 'public'}})
        clauses.append({
            'bool': {
                'should': [
                    {'bool': {'must_not': {'exists': {'field': 'end_embargo_date'}}}},
                    {'range': {'end_embargo_date': {'lte': today}}},
                ],
                'minimum_should_match': 1,
            }
        })
    elif getattr(user, 'is_superuser', False) or getattr(user, 'is_staff', False):
        pass
    else:
        user_group_names = list(user.groups.values_list('name', flat=True))
        allowed_data_types = ['public']
        if 'SensitiveDataGroup' in user_group_names:
            allowed_data_types.append('sensitive')
        if 'PrivateDataGroup' in user_group_names:
            allowed_data_types.append('private')

        embargo_clause = {
            'bool': {
                'should': [
                    {'bool': {'must_not': {'exists': {'field': 'end_embargo_date'}}}},
                    {'range': {'end_embargo_date': {'lte': today}}},
                    {'term': {'owner_id': user.id}},
                ],
                'minimum_should_match': 1,
            }
        }
        clauses.append({'terms': {'data_type': allowed_data_types}})
        clauses.append(embargo_clause)

    return clauses


def build_spatial_filter_clause(spatial_filter_value):
    if not spatial_filter_value:
        return None
    try:
        spatial_filters = json.loads(spatial_filter_value)
    except (TypeError, ValueError):
        return None

    if not spatial_filters:
        return None

    should_clauses = []
    for spatial_filter in spatial_filters:
        if not isinstance(spatial_filter, str):
            continue
        parts = spatial_filter.split(',')
        if len(parts) < 2:
            continue
        filter_type = parts[0]
        spatial_key = parts[1]

        if filter_type == 'group':
            should_clauses.append({'term': {'location_context_groups': spatial_key}})
            continue
        if filter_type != 'value' or len(parts) < 3:
            continue
        value = ','.join(parts[2:])
        should_clauses.append({'term': {'location_context_values': f'{spatial_key}|{value}'}})

    if not should_clauses:
        return None
    return {'bool': {'should': should_clauses, 'minimum_should_match': 1}}


def _coordinates_to_polygon_points(coordinates):
    points = []
    for coordinate in coordinates:
        if not isinstance(coordinate, (list, tuple)) or len(coordinate) < 2:
            return []
        try:
            points.append({'lon': float(coordinate[0]), 'lat': float(coordinate[1])})
        except (TypeError, ValueError):
            return []
    if points and (points[0]['lon'] != points[-1]['lon'] or points[0]['lat'] != points[-1]['lat']):
        points.append(dict(points[0]))
    return points


def build_polygon_filter_clause(polygon_value):
    if not polygon_value:
        return None
    try:
        polygon_data = json.loads(polygon_value)
    except (TypeError, ValueError):
        return None

    if isinstance(polygon_data, int):
        try:
            from bims.models import UserBoundary
            geometry = UserBoundary.objects.get(id=polygon_data).geometry
        except Exception:
            return None
        if geometry is None:
            return None
        geometry = geometry.clone()
        if geometry.srid and geometry.srid != 4326:
            geometry.transform(4326)
        if geometry.geom_type == 'Polygon':
            coordinates = geometry.coords[0]
        elif geometry.geom_type == 'MultiPolygon' and geometry.coords:
            coordinates = geometry.coords[0][0]
        else:
            return None
        points = _coordinates_to_polygon_points(coordinates)
    elif isinstance(polygon_data, list):
        points = _coordinates_to_polygon_points(polygon_data)
    else:
        return None

    if len(points) < 4:
        return None
    return {'geo_polygon': {'location': {'points': points}}}


def build_filter_clauses(params: dict, user, schema_name: str) -> list:
    clauses = [{'term': {'schema_name': schema_name}}]
    clauses += build_security_filter(user)

    taxon_ids = params.get('taxon', '')
    if taxon_ids:
        clauses.append({
            'terms': {'taxonomy_id': [int(t) for t in taxon_ids.split(',') if t]}
        })

    site_ids = params.get('siteId', '')
    if site_ids:
        clauses.append({
            'terms': {'site_id': [int(s) for s in site_ids.split(',') if s]}
        })

    modules = params.get('modules', '')
    if modules:
        clauses.append({
            'terms': {'module_group_id': [int(m) for m in modules.split(',') if m]}
        })

    spatial_clause = build_spatial_filter_clause(params.get('spatialFilter', ''))
    if spatial_clause:
        clauses.append(spatial_clause)

    ecosystem_type = params.get('ecosystemType', '')
    if ecosystem_type:
        values = [v for v in ecosystem_type.split(',') if v]
        if 'Unspecified' in values:
            values = [v.replace('Unspecified', '') for v in values]
        clauses.append({'terms': {'ecosystem_type': values}})

    cons_status = params.get('conservationStatus', '')
    if cons_status:
        try:
            statuses = json.loads(cons_status)
        except (ValueError, TypeError):
            statuses = [cons_status]
        if statuses:
            clauses.append({'terms': {'conservation_status': statuses}})

    endemic = params.get('endemic', '')
    if endemic:
        try:
            endemism_values = json.loads(endemic)
        except (ValueError, TypeError):
            endemism_values = [endemic]
        if endemism_values:
            clauses.append({'terms': {'endemism': endemism_values}})

    tags = params.get('tags', '')
    if tags:
        try:
            tag_list = json.loads(tags)
        except (ValueError, TypeError):
            tag_list = [t.strip() for t in tags.split(',') if t.strip()]
        if tag_list:
            clauses.append({'terms': {'tags': tag_list}})

    year_from = params.get('yearFrom', '')
    year_to = params.get('yearTo', '')
    if year_from or year_to:
        date_range = {}
        if year_from:
            date_range['gte'] = f'{year_from}-01-01'
        if year_to:
            date_range['lte'] = f'{year_to}-12-31'
        clauses.append({'range': {'collection_date': date_range}})

    bbox = params.get('bbox', '')
    if bbox:
        try:
            parts = [float(v) for v in bbox.split(',')]
            if len(parts) == 4:
                clauses.append({
                    'geo_bounding_box': {
                        'location': {
                            'top_left': {'lat': parts[3], 'lon': parts[0]},
                            'bottom_right': {'lat': parts[1], 'lon': parts[2]},
                        }
                    }
                })
        except ValueError:
            pass

    validated = params.get('validated', '')
    if validated == 'true':
        clauses.append({'term': {'is_validated': True}})
    elif validated == 'false':
        clauses.append({'term': {'is_validated': False}})

    polygon_clause = build_polygon_filter_clause(params.get('polygon', ''))
    if polygon_clause:
        clauses.append(polygon_clause)

    return clauses
