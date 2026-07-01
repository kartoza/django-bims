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
        from bims.opensearch.query_builder import build_filter_clauses, parse_extent
        current_schema = connection.schema_name

        # Resolve the effective requester - may differ from the logged-in user
        # when the frontend passes a requester_id param (mirrors legacy search).
        requester = user
        requester_id = params.get('requester_id', '')
        if requester_id and (user.is_superuser or user.is_staff):
            from django.contrib.auth import get_user_model
            try:
                requester = get_user_model().objects.get(id=int(requester_id))
            except (get_user_model().DoesNotExist, ValueError):
                pass

        filter_clauses = build_filter_clauses(params, requester, current_schema)

        # --- full-text search ---
        search_query = params.get('search', '').strip()

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
        extent = parse_extent(agg_data.get('extent', {}))

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

