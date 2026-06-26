import datetime
import json
import logging

from rest_framework.response import Response
from rest_framework import status

from bims.utils.api_view import BimsApiView

logger = logging.getLogger('bims')

MAX_PAGINATED_SITES = 20
MAX_PAGINATED_RECORDS = 50


class OpenSearchCollectionView(BimsApiView):
    """
    Search BiologicalCollectionRecord via OpenSearch.
    Accepts the same query parameters as /api/collection-search/ but
    queries the OpenSearch index instead of PostGIS directly.
    """

    def get(self, request):
        params = request.GET.dict()
        user = request.user
        fuzzy_search = False

        try:
            from bims.opensearch.client import get_client
            from bims.opensearch.indices import COLLECTIONS_INDEX
        except ImportError:
            return Response(
                {'detail': 'OpenSearch is not available.'},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        page = int(params.get('page', 1))
        page_size = int(params.get('page_size', MAX_PAGINATED_SITES))

        from django.db import connection
        current_schema = connection.schema_name

        # Always scope to the current tenant schema first.
        filter_clauses = [{'term': {'schema_name': current_schema}}]
        filter_clauses += self._build_security_filter(user)

        # --- full-text search ---
        search_query = params.get('search', '').strip()
        # --- taxon filter ---
        taxon_ids = params.get('taxon', '')
        if taxon_ids:
            filter_clauses.append({
                'terms': {'taxonomy_id': [int(t) for t in taxon_ids.split(',') if t]}
            })

        # --- site filter ---
        site_ids = params.get('siteId', '')
        if site_ids:
            filter_clauses.append({
                'terms': {'site_id': [int(s) for s in site_ids.split(',') if s]}
            })

        # --- module / taxon group filter ---
        modules = params.get('modules', '')
        if modules:
            filter_clauses.append({
                'terms': {'module_group_id': [int(m) for m in modules.split(',') if m]}
            })

        # --- ecosystem type ---
        ecosystem_type = params.get('ecosystemType', '')
        if ecosystem_type:
            values = [v for v in ecosystem_type.split(',') if v]
            if 'Unspecified' in values:
                values = [v.replace('Unspecified', '') for v in values]
            filter_clauses.append({'terms': {'ecosystem_type': values}})

        # --- conservation status ---
        conservation_status = params.get('conservationStatus', '')
        if conservation_status:
            import json as _json
            try:
                statuses = _json.loads(conservation_status)
            except (ValueError, TypeError):
                statuses = [conservation_status]
            if statuses:
                filter_clauses.append({'terms': {'conservation_status': statuses}})

        # --- endemism ---
        endemic = params.get('endemic', '')
        if endemic:
            import json as _json
            try:
                endemism_values = _json.loads(endemic)
            except (ValueError, TypeError):
                endemism_values = [endemic]
            if endemism_values:
                filter_clauses.append({'terms': {'endemism': endemism_values}})

        # --- tags ---
        tags = params.get('tags', '')
        if tags:
            import json as _json
            try:
                tag_list = _json.loads(tags)
            except (ValueError, TypeError):
                tag_list = [t.strip() for t in tags.split(',') if t.strip()]
            if tag_list:
                filter_clauses.append({'terms': {'tags': tag_list}})

        # --- date range ---
        year_from = params.get('yearFrom', '')
        year_to = params.get('yearTo', '')
        if year_from or year_to:
            date_range = {}
            if year_from:
                date_range['gte'] = f'{year_from}-01-01'
            if year_to:
                date_range['lte'] = f'{year_to}-12-31'
            filter_clauses.append({'range': {'collection_date': date_range}})

        # --- bounding box / polygon ---
        bbox = params.get('bbox', '')
        if bbox:
            parts = [float(v) for v in bbox.split(',')]
            if len(parts) == 4:
                filter_clauses.append({
                    'geo_bounding_box': {
                        'location': {
                            'top_left': {'lat': parts[3], 'lon': parts[0]},
                            'bottom_right': {'lat': parts[1], 'lon': parts[2]},
                        }
                    }
                })
        polygon_points = self._parse_polygon_points(params.get('polygon', ''))
        if polygon_points:
            filter_clauses.append({
                'geo_polygon': {
                    'location': {
                        'points': polygon_points,
                    }
                }
            })

        # --- validation ---
        validated = params.get('validated', '')
        if validated == 'true':
            filter_clauses.append({'term': {'is_validated': True}})
        elif validated == 'false':
            filter_clauses.append({'term': {'is_validated': False}})

        try:
            client = get_client()
        except Exception as exc:
            logger.error('OpenSearch client initialization failed: %s', exc)
            return Response(
                {'detail': 'Search service error.'},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        query = self._build_search_query(
            client=client,
            index_name=COLLECTIONS_INDEX,
            search_query=search_query,
            filter_clauses=filter_clauses,
        )
        fuzzy_search = query.get('_fuzzy_search', False)
        query.pop('_fuzzy_search', None)

        aggs = {
            'unique_sites': {'cardinality': {'field': 'site_id'}},
            'unique_taxa': {'cardinality': {'field': 'taxonomy_id'}},
            'extent': {
                'geo_bounds': {'field': 'location', 'wrap_longitude': True}
            },
            # All unique site_ids stored in SearchToken for Martin tiles.
            # size matches the search.max_buckets cluster setting (200000).
            'site_id_buckets': {
                'terms': {'field': 'site_id', 'size': 200000}
            },
            # Top sites for sidebar (record count per site).
            'top_sites': {
                'terms': {'field': 'site_id', 'size': MAX_PAGINATED_SITES},
                'aggs': {
                    'site_name': {'terms': {'field': 'site_name.keyword', 'size': 1}},
                    'site_code': {'terms': {'field': 'site_code.keyword', 'size': 1}},
                },
            },
            # Top taxa for sidebar (record count per taxon).
            'top_taxa': {
                'terms': {'field': 'taxonomy_id', 'size': MAX_PAGINATED_RECORDS},
                'aggs': {
                    'name': {'terms': {'field': 'canonical_name.keyword', 'size': 1}},
                },
            },
        }

        from_ = (page - 1) * page_size

        try:
            response = client.search(
                index=COLLECTIONS_INDEX,
                body={
                    'track_total_hits': True,
                    'query': query,
                    'aggs': aggs,
                    'from': from_,
                    'size': page_size,
                    '_source': [
                        'record_id', 'canonical_name', 'scientific_name',
                        'site_id', 'site_code', 'site_name', 'river_name',
                        'collection_date', 'ecosystem_type', 'location',
                        'module_group_name', 'data_type',
                    ],
                },
            )
        except Exception as exc:
            logger.error('OpenSearch query failed: %s', exc)
            return Response(
                {'detail': 'Search service error.'},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        hits = response['hits']
        total_hits = hits['total']['value']
        records = [h['_source'] for h in hits['hits']]

        agg_data = response.get('aggregations', {})
        unique_sites = agg_data.get('unique_sites', {}).get('value', 0)
        unique_taxa = agg_data.get('unique_taxa', {}).get('value', 0)
        extent = self._parse_extent(agg_data.get('extent', {}))

        site_id_buckets = agg_data.get('site_id_buckets', {})
        site_ids = [b['key'] for b in site_id_buckets.get('buckets', [])]
        token = self._create_search_token(site_ids, current_schema)

        sites = [
            {
                'site_id': b['key'],
                'name': (b['site_name']['buckets'][0]['key']
                         if b['site_name']['buckets'] else ''),
                'site_code': (b['site_code']['buckets'][0]['key']
                              if b['site_code']['buckets'] else ''),
                'total': b['doc_count'],
                'total_survey': 0,
            }
            for b in agg_data.get('top_sites', {}).get('buckets', [])
        ]

        taxa = [
            {
                'taxon_id': b['key'],
                'name': (b['name']['buckets'][0]['key']
                         if b['name']['buckets'] else ''),
                'total': b['doc_count'],
                'total_survey': 0,
            }
            for b in agg_data.get('top_taxa', {}).get('buckets', [])
        ]

        return Response({
            'status': 'finished',
            'fuzzy_search': fuzzy_search,
            'total': total_hits,
            'total_records': total_hits,
            'total_sites': unique_sites,
            'total_unique_taxa': unique_taxa,
            'page': page,
            'page_size': page_size,
            'extent': extent,
            'records': records,
            'sites': sites,
            'taxa': taxa,
            'token': str(token),
        })

    @staticmethod
    def _base_text_fields():
        return [
            'canonical_name^4',
            'scientific_name^3',
            'original_species_name^3',
            'vernacular_names^2',
            'site_code^2',
            'site_name^2',
            'river_name',
            'tags',
        ]

    def _build_search_query(self, client, index_name, search_query, filter_clauses):
        if not search_query:
            return {
                'bool': {
                    'must': [{'match_all': {}}],
                    'filter': filter_clauses,
                }
            }

        exact_phrase_query = {
            'bool': {
                'must': [{
                    'multi_match': {
                        'query': search_query,
                        'fields': self._base_text_fields(),
                        'type': 'phrase',
                    }
                }],
                'filter': filter_clauses,
            }
        }
        if self._query_has_hits(client, index_name, exact_phrase_query):
            return exact_phrase_query

        strict_query = {
            'bool': {
                'must': [{
                    'multi_match': {
                        'query': search_query,
                        'fields': self._base_text_fields(),
                        'type': 'best_fields',
                        'operator': 'and',
                    }
                }],
                'filter': filter_clauses,
            }
        }
        if self._query_has_hits(client, index_name, strict_query):
            return strict_query

        fuzzy_query = {
            'bool': {
                'must': [{
                    'multi_match': {
                        'query': search_query,
                        'fields': self._base_text_fields(),
                        'type': 'best_fields',
                        'fuzziness': 'AUTO',
                    }
                }],
                'filter': filter_clauses,
            },
            '_fuzzy_search': True,
        }
        return fuzzy_query

    @staticmethod
    def _query_has_hits(client, index_name, query):
        response = client.search(
            index=index_name,
            body={
                'size': 0,
                'track_total_hits': True,
                'query': query,
            },
        )
        return response.get('hits', {}).get('total', {}).get('value', 0) > 0

    @staticmethod
    def _create_search_token(site_ids: list, schema_name: str):
        from bims.models.search_token import SearchToken
        token = SearchToken.objects.create(
            schema_name=schema_name,
            site_ids=site_ids,
        )
        return token.token

    def _build_security_filter(self, user) -> list:
        """
        Build filter clauses that enforce data access rules:
        - public records are always visible
        - embargoed records are visible only to their owner
        - sensitive/private records are visible only if the user belongs
          to the corresponding group (handled downstream via data_type field)
        """
        today = datetime.date.today().strftime('%Y-%m-%d')
        clauses = []

        if user.is_anonymous:
            # Only public, non-embargoed records
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
        elif user.is_superuser or user.is_staff:
            pass  # no restrictions
        else:
            # Authenticated non-staff: public + own embargoed + group-accessible
            from django.contrib.auth.models import Group
            user_group_names = list(
                user.groups.values_list('name', flat=True)
            )
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

    @staticmethod
    def _parse_extent(geo_bounds: dict) -> list:
        bounds = geo_bounds.get('bounds', {})
        if not bounds:
            return []
        top_left = bounds.get('top_left', {})
        bottom_right = bounds.get('bottom_right', {})
        return [
            bottom_right.get('lon'),
            bottom_right.get('lat'),
            top_left.get('lon'),
            top_left.get('lat'),
        ]

    def _parse_polygon_points(self, polygon_value):
        if not polygon_value:
            return None
        try:
            polygon_data = json.loads(polygon_value)
        except (TypeError, ValueError):
            return None

        if isinstance(polygon_data, int):
            return self._get_user_boundary_polygon_points(polygon_data)

        if not isinstance(polygon_data, list):
            return None

        points = self._coordinates_to_polygon_points(polygon_data)
        return points if len(points) >= 4 else None

    def _get_user_boundary_polygon_points(self, boundary_id):
        try:
            from bims.models import UserBoundary
            geometry = UserBoundary.objects.get(id=boundary_id).geometry
        except Exception:
            return None

        if geometry is None:
            return None

        geometry = geometry.clone()
        if geometry.srid and geometry.srid != 4326:
            geometry.transform(4326)

        if geometry.geom_type == 'Polygon':
            coordinates = geometry.coords[0]
        elif geometry.geom_type == 'MultiPolygon' and len(geometry.coords) > 0:
            coordinates = geometry.coords[0][0]
        else:
            return None

        points = self._coordinates_to_polygon_points(coordinates)
        return points if len(points) >= 4 else None

    @staticmethod
    def _coordinates_to_polygon_points(coordinates):
        points = []
        for coordinate in coordinates:
            if not isinstance(coordinate, (list, tuple)) or len(coordinate) < 2:
                return []
            lon = coordinate[0]
            lat = coordinate[1]
            try:
                lon = float(lon)
                lat = float(lat)
            except (TypeError, ValueError):
                return []
            points.append({'lon': lon, 'lat': lat})

        if points and (points[0]['lon'] != points[-1]['lon'] or points[0]['lat'] != points[-1]['lat']):
            points.append(dict(points[0]))

        return points
