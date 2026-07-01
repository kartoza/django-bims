import json
import logging
import time

from celery import shared_task, current_task

logger = logging.getLogger('bims')

COUNT = 'count'
TOTAL_RECORDS = 'total_records'
TAXA_OCCURRENCE = 'taxa_occurrence'
CATEGORY_SUMMARY = 'category_summary'
BIODIVERSITY_DATA = 'biodiversity_data'
SITE_DETAILS = 'site_details'
OCCURRENCE_DATA = 'occurrence_data'
IUCN_NAME_LIST = 'iucn_name_list'
ORIGIN_NAME_LIST = 'origin_name_list'
SOURCE_REFERENCES = 'source_references'
CHEMICAL_RECORDS = 'chemical_records'
SURVEY = 'survey'

PER_YEAR_FREQUENCY = 'y'
PER_MONTH_FREQUENCY = 'm'


def _first_bucket_key(bucket, field, default=''):
    buckets = bucket.get(field, {}).get('buckets', [])
    return buckets[0]['key'] if buckets else default


def _build_query(filter_clauses):
    return {
        'bool': {
            'must': [{'match_all': {}}],
            'filter': filter_clauses,
        }
    }


def _run_os_aggregations(client, index_name, filter_clauses, data_frequency):
    from bims.opensearch.indices import COLLECTIONS_INDEX

    aggs = {
        'unique_sites': {'cardinality': {'field': 'site_id'}},
        'unique_taxa': {'cardinality': {'field': 'taxonomy_id'}},
        'extent': {'geo_bounds': {'field': 'location', 'wrap_longitude': True}},
        'by_origin': {'terms': {'field': 'origin', 'missing': 'unknown', 'size': 100}},
        'by_endemism': {'terms': {'field': 'endemism', 'missing': 'Unknown', 'size': 100}},
        'by_cons_status': {
            'terms': {'field': 'conservation_status', 'missing': 'NE', 'size': 50}
        },
        'by_national_cons_status': {
            'terms': {'field': 'national_conservation_status', 'missing': 'NE', 'size': 50}
        },
        'by_sampling_method': {
            'terms': {'field': 'sampling_method', 'missing': 'Unspecified', 'size': 200}
        },
        'by_biotope': {
            'terms': {'field': 'biotope', 'missing': 'Unspecified', 'size': 200}
        },
        'taxa_table': {
            'terms': {'field': 'taxonomy_id', 'size': 10000},
            'aggs': {
                'scientific_name': {
                    'terms': {'field': 'scientific_name.keyword', 'size': 1}
                },
                'origin': {
                    'terms': {'field': 'origin', 'missing': 'Unknown', 'size': 1}
                },
                'cons_status': {
                    'terms': {
                        'field': 'conservation_status', 'missing': 'Not evaluated', 'size': 1
                    }
                },
                'national_cons_status': {
                    'terms': {
                        'field': 'national_conservation_status',
                        'missing': 'Not evaluated',
                        'size': 1,
                    }
                },
                'endemism': {
                    'terms': {'field': 'endemism', 'missing': 'Unknown', 'size': 1}
                },
            },
        },
    }

    if data_frequency == PER_MONTH_FREQUENCY:
        aggs['by_date'] = {
            'date_histogram': {
                'field': 'collection_date',
                'calendar_interval': 'day',
                'format': 'yyyy-MM-dd',
                'min_doc_count': 1,
            }
        }
    else:
        aggs['by_year'] = {
            'date_histogram': {
                'field': 'collection_date',
                'calendar_interval': 'year',
                'format': 'yyyy',
                'min_doc_count': 1,
            }
        }

    return client.search(
        index=index_name,
        body={
            'size': 0,
            'track_total_hits': True,
            'query': _build_query(filter_clauses),
            'aggs': aggs,
        },
    )




def _taxa_occurrence_from_aggs(agg_data, data_frequency):
    result = {'occurrences_line_chart': {'values': [], 'keys': [], 'title': 'Occurrences'}}
    if data_frequency == PER_MONTH_FREQUENCY:
        buckets = agg_data.get('by_date', {}).get('buckets', [])
        result['occurrences_line_chart']['title'] = 'Occurrences per Date Sampled'
    else:
        buckets = agg_data.get('by_year', {}).get('buckets', [])

    for b in buckets:
        key = b['key_as_string']
        result['occurrences_line_chart']['keys'].append(
            key if data_frequency == PER_MONTH_FREQUENCY else int(key)
        )
        result['occurrences_line_chart']['values'].append(b['doc_count'])
    return result


def _category_summary_from_aggs(agg_data):
    return {
        b['key']: b['doc_count']
        for b in agg_data.get('by_origin', {}).get('buckets', [])
        if b['key'] != 'unknown'
    }


def _occurrence_data_from_aggs(agg_data):
    rows = []
    for b in agg_data.get('taxa_table', {}).get('buckets', []):
        rows.append({
            'taxon': _first_bucket_key(b, 'scientific_name'),
            'origin': _first_bucket_key(b, 'origin', 'Unknown'),
            'cons_status': _first_bucket_key(b, 'cons_status', 'Not evaluated'),
            'cons_status_national': _first_bucket_key(
                b, 'national_cons_status', 'Not evaluated'
            ),
            'endemism': _first_bucket_key(b, 'endemism', 'Unknown'),
            'count': b['doc_count'],
        })
    rows.sort(key=lambda r: r['taxon'])
    return rows


def _biodiversity_data_from_aggs(agg_data, iucn_colors, national_iucn_colors, project_name):
    def _chart(bucket_key, missing_label=None):
        buckets = agg_data.get(bucket_key, {}).get('buckets', [])
        keys, data = [], []
        for b in buckets:
            label = b['key']
            if missing_label and label == missing_label:
                label = missing_label
            keys.append(label)
            data.append(b['doc_count'])
        return {'keys': keys, 'data': data}

    origin_chart = _chart('by_origin')
    endemism_chart = _chart('by_endemism')

    cons_keys, cons_data = [], []
    for b in agg_data.get('by_cons_status', {}).get('buckets', []):
        cons_keys.append(b['key'])
        cons_data.append(b['doc_count'])

    nat_keys, nat_data = [], []
    for b in agg_data.get('by_national_cons_status', {}).get('buckets', []):
        nat_keys.append(b['key'])
        nat_data.append(b['doc_count'])

    sampling_chart = _chart('by_sampling_method')
    biotope_chart = _chart('by_biotope')

    biodiversity_data = {
        'times': {},
        'species': {
            'origin_chart': origin_chart,
            'endemism_chart': endemism_chart,
            'sampling_method_chart': sampling_chart,
            'biotope_chart': biotope_chart,
            'cons_status_chart': {
                'keys': cons_keys,
                'data': cons_data,
                'colours': [iucn_colors.get(k, '#cccccc') for k in cons_keys],
            },
        },
    }

    if project_name != 'fbis_africa':
        biodiversity_data['species']['cons_status_national_chart'] = {
            'keys': nat_keys,
            'data': nat_data,
            'colours': [national_iucn_colors.get(k, '#cccccc') for k in nat_keys],
        }

    return biodiversity_data


@shared_task(
    bind=True,
    name='bims.tasks.opensearch_location_site_summary',
    queue='search',
)
def opensearch_location_site_summary(self, filters, search_process_id):
    from preferences import preferences
    from bims.models import (
        IUCNStatus, TaxonGroup, SearchProcess, SEARCH_FINISHED, TaxonOrigin,
    )
    from bims.opensearch.client import get_client
    from bims.opensearch.indices import COLLECTIONS_INDEX
    from bims.opensearch.query_builder import build_filter_clauses, parse_extent
    from bims.utils.search_process import create_search_process_file

    called_directly = current_task.request.called_directly
    if not called_directly:
        self.update_state(
            state='PROGRESS',
            meta={'process': 'Generating OpenSearch location site summary'},
        )

    search_process = SearchProcess.objects.get(id=search_process_id)
    filters = dict(filters)
    requester = search_process.requester
    site_id = filters.get('siteId', '')
    data_frequency = filters.get('d', PER_YEAR_FREQUENCY)

    from django.db import connection
    schema_name = connection.schema_name

    t0 = time.time()
    client = get_client()
    filter_clauses = build_filter_clauses(filters, requester, schema_name)

    try:
        os_response = _run_os_aggregations(
            client, COLLECTIONS_INDEX, filter_clauses, data_frequency
        )
    except Exception as exc:
        logger.error('OpenSearch aggregation failed: %s', exc)
        raise

    agg_data = os_response.get('aggregations', {})
    total_records = os_response['hits']['total']['value']

    iucn_colors = dict(
        IUCNStatus.objects.filter(national=False).values_list('category', 'colour')
    )
    national_iucn_colors = dict(
        IUCNStatus.objects.filter(national=True).values_list('category', 'colour')
    )
    iucn_category = dict((x, y) for x, y in IUCNStatus.CATEGORY_CHOICES)
    origin_name_list = {
        o.origin_key: o.category for o in TaxonOrigin.objects.all()
    }

    taxa_occurrence = _taxa_occurrence_from_aggs(agg_data, data_frequency)
    category_summary = _category_summary_from_aggs(agg_data)
    occurrence_data = _occurrence_data_from_aggs(agg_data)
    biodiversity_data = _biodiversity_data_from_aggs(
        agg_data,
        iucn_colors,
        national_iucn_colors,
        getattr(preferences.SiteSetting, 'project_name', ''),
    )
    extent = parse_extent(agg_data.get('extent', {}))

    is_multi_sites = not bool(site_id)
    unique_sites = agg_data.get('unique_sites', {}).get('value', 0)
    unique_taxa = agg_data.get('unique_taxa', {}).get('value', 0)

    if is_multi_sites:
        site_details = {
            'overview': {
                'Occurences': total_records,
                'Number of Sites': unique_sites,
                'Number of Taxa': unique_taxa,
            }
        }
    else:
        from bims.utils.location_site import overview_site_detail
        site_details = overview_site_detail(int(site_id))
        site_details['Species and Occurences'] = {
            'Number of Occurrences': str(total_records),
            'Number of Taxa': str(unique_taxa),
        }

    # DB-backed parts: source references, chemical records, surveys, site images.
    # Use a lightweight CollectionSearch scoped to the same filters.
    from bims.api_views.search import CollectionSearch
    from sorl.thumbnail import get_thumbnail
    from django.db.models import Q

    search = CollectionSearch(
        filters,
        requester.id if requester else None,
    )
    collection_results = search.process_search()

    source_references = []
    try:
        collection_with_references = collection_results.exclude(
            source_reference__isnull=True
        ).distinct('source_reference')
        source_references = collection_with_references.source_references()

        collection_with_dataset_keys = collection_results.exclude(
            dataset_key__isnull=True
        ).distinct('dataset_key')
        dataset_source_references = collection_with_dataset_keys.dataset_source_references()

        if dataset_source_references:
            source_references = [
                ref for ref in source_references
                if not (
                    ref.get('Reference Category') == 'Database' and
                    'gbif' in ref.get('Source', '').lower()
                )
            ]
        source_references += dataset_source_references
    except Exception as exc:
        logger.warning('Could not fetch source references: %s', exc)

    list_chems = {}
    chem_exist = False
    if site_id:
        from bims.models import ChemicalRecord
        from bims.serializers.chemical_records_serializer import ChemicalRecordsSerializer
        list_chems_code = ['COND', 'TEMP', 'PH', 'DO']
        chems = ChemicalRecord.objects.filter(
            Q(location_site_id=site_id) | Q(survey__site_id=site_id)
        )
        if chems.exists():
            chem_exist = True
        chems_source_references = chems.source_references()
        if chems_source_references:
            existing_ids = [ref['ID'] for ref in source_references]
            for csr in chems_source_references:
                if 'ID' in csr and csr['ID'] not in existing_ids:
                    source_references.append(csr)
        x_label = []
        for chem in list_chems_code:
            chem_name = chem.lower().replace('-n', '').upper()
            qs = chems.filter(chem__chem_code=chem).order_by('date')
            if not qs.exists():
                continue
            value = ChemicalRecordsSerializer(qs, many=True)
            chem_unit = qs[0].chem.chem_unit.unit
            data = {
                'unit': chem_unit,
                'name': qs[0].chem.chem_description,
                'values': value.data,
            }
            for val in value.data:
                if val['str_date'] not in x_label:
                    x_label.append(val['str_date'])
            list_chems.setdefault(chem_name, []).append({chem: data})
        list_chems['x_label'] = x_label

    from bims.models import Survey, BiologicalCollectionRecord
    surveys = Survey.objects.filter(
        id__in=collection_results.values('survey')
    ).order_by('-date')
    survey_list = []
    for survey in surveys[:5]:
        survey_list.append({
            'date': str(survey.date),
            'site': str(survey.site),
            'id': survey.id,
            'records': BiologicalCollectionRecord.objects.filter(
                survey=survey
            ).count(),
        })

    site_images = []
    if not is_multi_sites:
        from bims.models import SiteImage
        site_image_objects = SiteImage.objects.filter(
            Q(survey__in=list(
                collection_results.distinct('survey').values_list(
                    'survey__id', flat=True
                )
            )) | Q(site_id=int(site_id))
        ).values_list('image', flat=True)
        for img in site_image_objects:
            try:
                site_images.append(
                    get_thumbnail(img, 'x500', crop='center', quality=99).url
                )
            except Exception:
                pass

    is_sass_exists = collection_results.filter(
        notes__icontains='sass'
    ).exists()

    modules = []
    module_filter = filters.get('modules', '')
    if module_filter:
        module_ids = []
        if isinstance(module_filter, str):
            if ',' in module_filter:
                module_ids = [int(x) for x in module_filter.split(',') if x.isdigit()]
            elif module_filter.isdigit():
                module_ids = [int(module_filter)]
        if module_ids:
            from bims.enums import TaxonomicGroupCategory
            modules = list(
                TaxonGroup.objects.filter(
                    category=TaxonomicGroupCategory.SPECIES_MODULE.name,
                    id__in=module_ids,
                ).values_list('name', flat=True)
            )

    try:
        from bims.models import DashboardConfiguration
        dashboard_configuration = json.loads(
            DashboardConfiguration.objects.get(
                module_group__id=filters['modules']
            ).additional_data
        )
    except Exception:
        dashboard_configuration = {}

    search_process.set_status(SEARCH_FINISHED, False)

    response_data = {
        TOTAL_RECORDS: total_records,
        SITE_DETAILS: site_details,
        TAXA_OCCURRENCE: taxa_occurrence,
        CATEGORY_SUMMARY: category_summary,
        OCCURRENCE_DATA: occurrence_data,
        IUCN_NAME_LIST: iucn_category,
        ORIGIN_NAME_LIST: origin_name_list,
        BIODIVERSITY_DATA: biodiversity_data,
        SOURCE_REFERENCES: source_references,
        CHEMICAL_RECORDS: list_chems,
        SURVEY: survey_list,
        'modules': modules,
        'site_images': site_images,
        'process': search_process.process_id,
        'extent': extent,
        'sites_raw_query': search_process.process_id,
        'is_multi_sites': is_multi_sites,
        'is_sass_exists': is_sass_exists,
        'is_chem_exists': chem_exist,
        'total_survey': surveys.count(),
        'dashboard_configuration': dashboard_configuration,
        'times': {'total': time.time() - t0},
    }

    if not called_directly:
        self.update_state(state='SUCCESS')

    create_search_process_file(
        response_data, search_process, file_path=None, finished=True
    )
    return response_data
