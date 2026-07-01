import logging
from collections import OrderedDict

from celery import shared_task

logger = logging.getLogger('bims')

SPECIES_RANKS = ['SPECIES', 'SUBSPECIES', 'VARIETY']


def _run_overview_aggregation(client, index_name, filter_clauses):
    return client.search(
        index=index_name,
        body={
            'size': 0,
            'query': {'bool': {'must': [{'match_all': {}}], 'filter': filter_clauses}},
            'aggs': {
                'by_module': {
                    'terms': {'field': 'module_group_id', 'size': 200},
                    'aggs': {
                        'unique_sites': {'cardinality': {'field': 'site_id'}},
                        'unique_taxa': {'cardinality': {'field': 'taxonomy_id'}},
                        'by_endemism': {
                            'terms': {
                                'field': 'endemism',
                                'missing': 'Unknown',
                                'size': 100,
                            }
                        },
                        'by_origin': {
                            'terms': {
                                'field': 'origin',
                                'missing': 'Unknown',
                                'size': 100,
                            }
                        },
                        'accepted_species': {
                            'filter': {
                                'bool': {
                                    'must': [
                                        {'term': {'taxonomy_status': 'ACCEPTED'}},
                                        {'terms': {'taxonomy_rank': SPECIES_RANKS}},
                                    ]
                                }
                            },
                            'aggs': {
                                'by_cons_status': {
                                    'terms': {
                                        'field': 'conservation_status',
                                        'missing': 'Not evaluated',
                                        'size': 50,
                                    }
                                }
                            },
                        },
                    },
                }
            },
        },
    )


@shared_task(
    name='bims.tasks.opensearch_location_sites_overview',
    queue='search',
)
def opensearch_location_sites_overview(
    search_parameters=None,
    search_process_id=None,
):
    from bims.models import (
        TaxonGroup,
        IUCNStatus,
        SearchProcess,
    )
    from bims.models.search_process import SEARCH_PROCESSING, SEARCH_FINISHED
    from bims.enums import TaxonomicGroupCategory
    from bims.opensearch.client import get_client
    from bims.opensearch.indices import COLLECTIONS_INDEX
    from bims.opensearch.query_builder import build_filter_clauses
    from bims.api_views.location_site_overview import LocationSiteOverviewData
    from django.db import connection

    if search_parameters is None:
        search_parameters = {}

    try:
        search_process = SearchProcess.objects.get(id=search_process_id)
    except SearchProcess.DoesNotExist:
        return

    search_process.set_status(SEARCH_PROCESSING)
    requester = search_process.requester
    schema_name = connection.schema_name

    params = dict(search_parameters)
    filter_clauses = build_filter_clauses(params, requester, schema_name)

    client = get_client()
    response = _run_overview_aggregation(client, COLLECTIONS_INDEX, filter_clauses)
    agg_data = response.get('aggregations', {})

    iucn_colours = dict(
        IUCNStatus.objects.values_list('category', 'colour')
    )
    iucn_names = dict(IUCNStatus.CATEGORY_CHOICES)

    buckets_by_id = {
        b['key']: b
        for b in agg_data.get('by_module', {}).get('buckets', [])
    }

    groups = TaxonGroup.objects.filter(
        category=TaxonomicGroupCategory.SPECIES_MODULE.name
    ).order_by('display_order')

    biodiversity_data = OrderedDict()
    for group in groups:
        bucket = buckets_by_id.get(group.id, {})
        doc_count = bucket.get('doc_count', 0)

        endemism = [
            {'endemism_name': b['key'], 'count': b['doc_count']}
            for b in bucket.get('by_endemism', {}).get('buckets', [])
        ]
        origin = [
            {'origin_name': b['key'], 'name': b['key'], 'count': b['doc_count']}
            for b in bucket.get('by_origin', {}).get('buckets', [])
            if b['key'] != 'Unknown'
        ]
        cons_status = []
        for b in (
            bucket.get('accepted_species', {})
            .get('by_cons_status', {})
            .get('buckets', [])
        ):
            cat = b['key']
            entry = {
                'iucn_category': cat,
                'colour': iucn_colours.get(cat, '#cccccc'),
                'count': b['doc_count'],
            }
            if cat in iucn_names:
                entry['name'] = iucn_names[cat]
            cons_status.append(entry)

        group_data = {
            LocationSiteOverviewData.MODULE: group.id,
            LocationSiteOverviewData.GROUP_OCCURRENCES: doc_count,
            LocationSiteOverviewData.GROUP_SITES: (
                bucket.get('unique_sites', {}).get('value', 0)
            ),
            LocationSiteOverviewData.GROUP_NUM_OF_TAXA: (
                bucket.get('unique_taxa', {}).get('value', 0)
            ),
            LocationSiteOverviewData.GROUP_ENDEMISM: endemism,
            LocationSiteOverviewData.GROUP_ORIGIN: origin,
            LocationSiteOverviewData.GROUP_CONS_STATUS: cons_status,
        }
        try:
            from sorl.thumbnail import get_thumbnail
            group_data[LocationSiteOverviewData.GROUP_ICON] = get_thumbnail(
                group.logo, 'x140', crop='center'
            ).name
        except Exception:
            pass

        biodiversity_data[group.name] = group_data

    # Source references still require a DB query
    source_references = []
    try:
        from bims.api_views.search import CollectionSearch
        search = CollectionSearch(params, requester.id if requester else None)
        collection_results = search.process_search()
        collection_with_refs = collection_results.exclude(
            source_reference__isnull=True
        ).distinct('source_reference')
        source_references = collection_with_refs.source_references()
    except Exception as exc:
        logger.warning('Could not fetch source references: %s', exc)

    biodiversity_data['source_references'] = source_references

    results = {
        LocationSiteOverviewData.BIODIVERSITY_DATA: biodiversity_data,
        LocationSiteOverviewData.SASS_EXIST: False,
        LocationSiteOverviewData.CLIMATE_EXIST: False,
    }

    search_process.set_status(SEARCH_FINISHED, False)
    search_process.save_to_file(results)
