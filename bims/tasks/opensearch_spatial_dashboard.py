import logging
from collections import defaultdict

from celery import shared_task

logger = logging.getLogger('bims')

SPECIES_RANKS = ['SPECIES', 'SUBSPECIES', 'VARIETY']
_EXCLUDED_CONS_CATEGORIES = {'DD', 'DDD', 'DDT', 'NE', ''}


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def _get_filter_clauses(search_parameters, search_process):
    from bims.opensearch.query_builder import build_filter_clauses
    from django.db import connection
    requester = search_process.requester
    schema_name = connection.schema_name
    params = dict(search_parameters)
    return build_filter_clauses(params, requester, schema_name)


def _run_search(client, index_name, filter_clauses, aggs, size=0):
    return client.search(
        index=index_name,
        body={
            'size': size,
            'query': {'bool': {'filter': filter_clauses}},
            'aggs': aggs,
        },
    )


def _get_taxa_ids_for_rli(client, index_name, filter_clauses):
    """Return {taxonomy_id: set(module_group_id)} for RLI-eligible taxa."""
    response = _run_search(
        client, index_name, filter_clauses,
        aggs={
            'rli_taxa': {
                'filter': {
                    'bool': {
                        'must': [
                            {'term': {'taxonomy_status': 'ACCEPTED'}},
                            {'terms': {'taxonomy_rank': SPECIES_RANKS}},
                            {'term': {'origin': 'indigenous'}},
                            {'term': {'include_in_rli': True}},
                        ]
                    }
                },
                'aggs': {
                    'by_module': {
                        'terms': {'field': 'module_group_id', 'size': 200},
                        'aggs': {
                            'taxa_ids': {'terms': {'field': 'taxonomy_id', 'size': 10000}},
                        },
                    }
                },
            }
        },
    )
    taxa_to_module_ids = defaultdict(set)
    for mod_bucket in (
        response.get('aggregations', {})
        .get('rli_taxa', {})
        .get('by_module', {})
        .get('buckets', [])
    ):
        mod_id = mod_bucket['key']
        for t_bucket in mod_bucket.get('taxa_ids', {}).get('buckets', []):
            taxa_to_module_ids[t_bucket['key']].add(mod_id)
    return taxa_to_module_ids


# ---------------------------------------------------------------------------
# opensearch_spatial_dashboard_summary
# ---------------------------------------------------------------------------

@shared_task(
    name='bims.tasks.opensearch_spatial_dashboard_summary',
    queue='search',
)
def opensearch_spatial_dashboard_summary(search_parameters=None, search_process_id=None):
    from collections import OrderedDict
    from bims.models import TaxonGroup, IUCNStatus, SearchProcess
    from bims.models.search_process import SEARCH_PROCESSING, SEARCH_FINISHED
    from bims.opensearch.client import get_client
    from bims.opensearch.indices import COLLECTIONS_INDEX
    from bims.enums import TaxonomicGroupCategory

    if search_parameters is None:
        search_parameters = {}

    try:
        search_process = SearchProcess.objects.get(id=search_process_id)
    except SearchProcess.DoesNotExist:
        return

    search_process.set_status(SEARCH_PROCESSING)

    filter_clauses = _get_filter_clauses(search_parameters, search_process)
    client = get_client()

    response = _run_search(
        client, COLLECTIONS_INDEX, filter_clauses,
        aggs={
            'by_module': {
                'terms': {'field': 'module_group_id', 'size': 200},
                'aggs': {
                    'unique_taxa': {'cardinality': {'field': 'taxonomy_id'}},
                    'by_origin': {
                        'terms': {'field': 'origin', 'missing': 'Unknown', 'size': 50},
                        'aggs': {'unique_taxa': {'cardinality': {'field': 'taxonomy_id'}}},
                    },
                    'by_endemism': {
                        'terms': {'field': 'endemism', 'missing': 'Unknown', 'size': 50},
                        'aggs': {'unique_taxa': {'cardinality': {'field': 'taxonomy_id'}}},
                    },
                    'by_cons_global': {
                        'terms': {
                            'field': 'conservation_status',
                            'missing': 'NE',
                            'size': 50,
                        },
                        'aggs': {'unique_taxa': {'cardinality': {'field': 'taxonomy_id'}}},
                    },
                    'by_cons_national': {
                        'terms': {
                            'field': 'national_conservation_status',
                            'missing': 'NE',
                            'size': 50,
                        },
                        'aggs': {'unique_taxa': {'cardinality': {'field': 'taxonomy_id'}}},
                    },
                },
            }
        },
    )

    groups = TaxonGroup.objects.filter(
        category=TaxonomicGroupCategory.SPECIES_MODULE.name
    ).order_by('display_order')
    module_names = [g.name for g in groups]
    group_name_by_id = {g.id: g.name for g in groups}

    iucn_labels = dict(IUCNStatus.CATEGORY_CHOICES)

    overview = {'Number of Taxa': {}}
    origin = {}
    endemism = {}
    cons_global = {}
    cons_national = {}

    for bucket in response.get('aggregations', {}).get('by_module', {}).get('buckets', []):
        mod_id = bucket['key']
        mod_name = group_name_by_id.get(mod_id)
        if not mod_name:
            continue

        overview['Number of Taxa'][mod_name] = (
            bucket.get('unique_taxa', {}).get('value', 0)
        )

        for sub_bucket in bucket.get('by_origin', {}).get('buckets', []):
            key = sub_bucket['key'] if sub_bucket['key'] != 'Unknown' else 'Unknown'
            count = sub_bucket.get('unique_taxa', {}).get('value', 0)
            origin.setdefault(key, {})[mod_name] = count

        for sub_bucket in bucket.get('by_endemism', {}).get('buckets', []):
            key = sub_bucket['key']
            count = sub_bucket.get('unique_taxa', {}).get('value', 0)
            endemism.setdefault(key, {})[mod_name] = count

        for sub_bucket in bucket.get('by_cons_global', {}).get('buckets', []):
            raw = sub_bucket['key']
            label = iucn_labels.get(raw, raw)
            count = sub_bucket.get('unique_taxa', {}).get('value', 0)
            cons_global.setdefault(label, {})[mod_name] = count

        for sub_bucket in bucket.get('by_cons_national', {}).get('buckets', []):
            raw = sub_bucket['key']
            label = iucn_labels.get(raw, raw)
            count = sub_bucket.get('unique_taxa', {}).get('value', 0)
            cons_national.setdefault(label, {})[mod_name] = count

    # Ensure every module appears in every row (fill zeros)
    for section in [overview, origin, endemism, cons_global, cons_national]:
        for row_values in section.values():
            if not isinstance(row_values, dict):
                continue
            for mod in module_names:
                row_values.setdefault(mod, 0)

    results = {
        'modules': module_names,
        'overview': overview,
        'origin': origin,
        'endemism': endemism,
        'cons_status_global': cons_global,
        'cons_status_national': cons_national,
    }
    search_process.set_status(SEARCH_FINISHED, False)
    search_process.save_to_file(results)


# ---------------------------------------------------------------------------
# opensearch_spatial_dashboard_cons_status
# ---------------------------------------------------------------------------

@shared_task(
    name='bims.tasks.opensearch_spatial_dashboard_cons_status',
    queue='search',
)
def opensearch_spatial_dashboard_cons_status(search_parameters=None, search_process_id=None):
    from bims.models import TaxonGroup, IUCNStatus, SearchProcess
    from bims.models.search_process import SEARCH_PROCESSING, SEARCH_FINISHED
    from bims.opensearch.client import get_client
    from bims.opensearch.indices import COLLECTIONS_INDEX
    from bims.enums import TaxonomicGroupCategory

    if search_parameters is None:
        search_parameters = {}

    try:
        search_process = SearchProcess.objects.get(id=search_process_id)
    except SearchProcess.DoesNotExist:
        return

    search_process.set_status(SEARCH_PROCESSING)

    filter_clauses = _get_filter_clauses(search_parameters, search_process)
    client = get_client()

    response = _run_search(
        client, COLLECTIONS_INDEX, filter_clauses,
        aggs={
            'by_module': {
                'terms': {'field': 'module_group_id', 'size': 200},
                'aggs': {
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
                    }
                },
            }
        },
    )

    groups = TaxonGroup.objects.filter(
        category=TaxonomicGroupCategory.SPECIES_MODULE.name
    ).order_by('display_order')
    group_name_by_id = {g.id: g.name for g in groups}

    iucn_colours = dict(IUCNStatus.objects.values_list('category', 'colour'))
    iucn_names = dict(IUCNStatus.CATEGORY_CHOICES)

    modules = []
    for bucket in response.get('aggregations', {}).get('by_module', {}).get('buckets', []):
        mod_id = bucket['key']
        mod_name = group_name_by_id.get(mod_id)
        if not mod_name:
            continue
        cleaned = []
        for sub_bucket in (
            bucket.get('accepted_species', {})
            .get('by_cons_status', {})
            .get('buckets', [])
        ):
            cat = sub_bucket['key']
            if cat in _EXCLUDED_CONS_CATEGORIES:
                continue
            cleaned.append({
                'name': iucn_names.get(cat, cat),
                'count': sub_bucket['doc_count'],
                'colour': iucn_colours.get(cat),
                'category': cat,
            })
        modules.append({'name': mod_name, 'cons_status': cleaned})

    search_process.set_status(SEARCH_FINISHED, False)
    search_process.save_to_file({'modules': modules})


# ---------------------------------------------------------------------------
# opensearch_spatial_dashboard_map
# ---------------------------------------------------------------------------

@shared_task(
    name='bims.tasks.opensearch_spatial_dashboard_map',
    queue='search',
)
def opensearch_spatial_dashboard_map(search_parameters=None, search_process_id=None):
    """
    Get map extent from OpenSearch geo_bounds.
    Still creates a PostgreSQL view for the GeoServer WMS site layer.
    """
    from bims.models import SearchProcess
    from bims.models.search_process import SEARCH_PROCESSING, SEARCH_FINISHED
    from bims.opensearch.client import get_client
    from bims.opensearch.indices import COLLECTIONS_INDEX
    from bims.opensearch.query_builder import parse_extent
    from bims.api_views.search import CollectionSearch

    if search_parameters is None:
        search_parameters = {}

    try:
        search_process = SearchProcess.objects.get(id=search_process_id)
    except SearchProcess.DoesNotExist:
        return

    search_process.set_status(SEARCH_PROCESSING)

    filter_clauses = _get_filter_clauses(search_parameters, search_process)
    client = get_client()

    response = _run_search(
        client, COLLECTIONS_INDEX, filter_clauses,
        aggs={'extent': {'geo_bounds': {'field': 'location', 'wrap_longitude': True}}},
    )

    extent = parse_extent(response.get('aggregations', {}).get('extent', {}))

    # Still need the DB view for GeoServer WMS site layer
    if search_process.requester and 'requester' not in search_parameters:
        search_parameters = dict(search_parameters)
        search_parameters['requester'] = search_process.requester.id

    view_name = None
    try:
        search = CollectionSearch(search_parameters)
        search.process_search()
        if search.location_sites_raw_query:
            search_process.set_search_raw_query(search.location_sites_raw_query)
            search_process.create_view()
            view_name = search_process.process_id
    except Exception as exc:
        logger.warning('Could not create GeoServer view: %s', exc)

    search_process.set_status(SEARCH_FINISHED, False)
    search_process.save_to_file({'extent': extent, 'sites_raw_query': view_name})


# ---------------------------------------------------------------------------
# opensearch_spatial_dashboard_rli
# ---------------------------------------------------------------------------

@shared_task(
    name='bims.tasks.opensearch_spatial_dashboard_rli',
    queue='search',
)
def opensearch_spatial_dashboard_rli(search_parameters=None, search_process_id=None):
    """
    RLI computation using OpenSearch for the initial taxa filter.
    Assessment history still comes from IUCNAssessment (PostgreSQL).
    """
    from datetime import date
    from django.db.models import Q
    from bims.models import Taxonomy, SearchProcess
    from bims.models.iucn_assessment import IUCNAssessment
    from bims.models.search_process import SEARCH_PROCESSING, SEARCH_FINISHED
    from bims.opensearch.client import get_client
    from bims.opensearch.indices import COLLECTIONS_INDEX
    from bims.tasks.spatial_dashboard import _compute_rli, _build_rli_output

    DD_CATEGORIES = {'DD', 'DDD', 'DDT'}

    if search_parameters is None:
        search_parameters = {}

    try:
        search_process = SearchProcess.objects.get(id=search_process_id)
    except SearchProcess.DoesNotExist:
        return

    search_process.set_status(SEARCH_PROCESSING)

    filter_clauses = _get_filter_clauses(search_parameters, search_process)
    client = get_client()

    taxa_to_module_ids = _get_taxa_ids_for_rli(client, COLLECTIONS_INDEX, filter_clauses)

    if not taxa_to_module_ids:
        results = {
            'series': [],
            'aggregate': [],
            'metadata': {'total_taxa': 0, 'total_assessed': 0, 'total_dd': 0, 'total_ne': 0},
        }
        search_process.set_status(SEARCH_FINISHED, False)
        search_process.save_to_file(results)
        return

    # Map module IDs to names
    from bims.models import TaxonGroup
    from bims.enums import TaxonomicGroupCategory
    module_name_by_id = dict(
        TaxonGroup.objects.filter(
            category=TaxonomicGroupCategory.SPECIES_MODULE.name
        ).values_list('id', 'name')
    )

    taxa_to_modules = defaultdict(set)
    for tid, mod_ids in taxa_to_module_ids.items():
        for mid in mod_ids:
            taxa_to_modules[tid].add(module_name_by_id.get(mid, 'Unknown'))

    taxonomy_ids = list(taxa_to_modules.keys())

    assessments = list(
        IUCNAssessment.objects.filter(
            taxonomy_id__in=taxonomy_ids,
            year_published__isnull=False,
        ).values('taxonomy_id', 'year_published', 'red_list_category_code')
        .order_by('taxonomy_id', 'year_published')
    )

    taxon_timelines = defaultdict(list)
    all_years = set()
    for a in assessments:
        cat = (a['red_list_category_code'] or '').strip()
        year = a['year_published']
        if year and cat:
            taxon_timelines[a['taxonomy_id']].append((year, cat))
            all_years.add(year)

    if all_years:
        year_taxa_statuses = defaultdict(list)
        for tid, timeline in taxon_timelines.items():
            for assess_year, cat in timeline:
                year_taxa_statuses[assess_year].append((tid, cat))
        per_module_year, aggregate_year = _compute_rli(
            taxa_to_modules, dict(year_taxa_statuses), DD_CATEGORIES, use_fixed_pool=True,
        )
    else:
        taxa_with_status = Taxonomy.objects.filter(
            id__in=taxonomy_ids,
            iucn_status__isnull=False,
        ).values('id', 'iucn_status__category')
        current_year = date.today().year
        statuses = [(r['id'], r['iucn_status__category'] or '') for r in taxa_with_status]
        year_taxa_statuses = {current_year: statuses}
        per_module_year, aggregate_year = _compute_rli(
            taxa_to_modules, year_taxa_statuses, DD_CATEGORIES
        )

    series, aggregate = _build_rli_output(per_module_year, aggregate_year)

    total_dd = Taxonomy.objects.filter(
        id__in=taxonomy_ids, iucn_status__category__in=list(DD_CATEGORIES)
    ).count()
    total_ne = Taxonomy.objects.filter(id__in=taxonomy_ids).filter(
        Q(iucn_status__category='NE') |
        Q(iucn_status__isnull=True) |
        Q(iucn_status__category='')
    ).count()

    search_process.set_status(SEARCH_FINISHED, False)
    search_process.save_to_file({
        'series': series,
        'aggregate': aggregate,
        'metadata': {
            'total_taxa': len(taxonomy_ids),
            'total_dd': total_dd,
            'total_ne': total_ne,
        },
    })


# ---------------------------------------------------------------------------
# opensearch_spatial_dashboard_national_cons_status
# ---------------------------------------------------------------------------

@shared_task(
    name='bims.tasks.opensearch_spatial_dashboard_national_cons_status',
    queue='search',
)
def opensearch_spatial_dashboard_national_cons_status(
    search_parameters=None, search_process_id=None
):
    from bims.models import TaxonGroup, SearchProcess
    from bims.models.search_process import SEARCH_PROCESSING, SEARCH_FINISHED
    from bims.opensearch.client import get_client
    from bims.opensearch.indices import COLLECTIONS_INDEX
    from bims.models.taxon_conservation_assessment import TaxonNationalConservationAssessment
    from bims.scripts.species_keys import SANBI_2016_BACKCAST, SANBI_2026_REDLIST
    from bims.tasks.spatial_dashboard import _compute_rli
    from bims.enums import TaxonomicGroupCategory

    DD_CATEGORIES = {'DD', 'DDD', 'DDT'}
    ASSESSMENT_ORDER = [SANBI_2016_BACKCAST, SANBI_2026_REDLIST]

    if search_parameters is None:
        search_parameters = {}

    try:
        search_process = SearchProcess.objects.get(id=search_process_id)
    except SearchProcess.DoesNotExist:
        return

    search_process.set_status(SEARCH_PROCESSING)

    filter_clauses = _get_filter_clauses(search_parameters, search_process)
    client = get_client()

    taxa_to_module_ids = _get_taxa_ids_for_rli(client, COLLECTIONS_INDEX, filter_clauses)

    if not taxa_to_module_ids:
        search_process.set_status(SEARCH_FINISHED, False)
        search_process.save_to_file({'series': [], 'aggregate': []})
        return

    module_name_by_id = dict(
        TaxonGroup.objects.filter(
            category=TaxonomicGroupCategory.SPECIES_MODULE.name
        ).values_list('id', 'name')
    )

    taxa_to_modules = defaultdict(set)
    for tid, mod_ids in taxa_to_module_ids.items():
        for mid in mod_ids:
            taxa_to_modules[tid].add(module_name_by_id.get(mid, 'Unknown'))

    taxonomy_ids = list(taxa_to_modules.keys())

    national_rows = (
        TaxonNationalConservationAssessment.objects
        .filter(taxonomy_id__in=taxonomy_ids)
        .exclude(iucn_status__isnull=True)
        .values('taxonomy_id', 'assessment_label', 'iucn_status__category')
    )
    assessment_statuses = defaultdict(list)
    for row in national_rows:
        label = row['assessment_label']
        if label in (SANBI_2016_BACKCAST, SANBI_2026_REDLIST):
            assessment_statuses[label].append(
                (row['taxonomy_id'], row['iucn_status__category'] or '')
            )

    label_to_idx = {label: idx for idx, label in enumerate(ASSESSMENT_ORDER)}
    year_taxa_statuses = {
        label_to_idx[label]: statuses
        for label, statuses in assessment_statuses.items()
        if label in label_to_idx
    }

    per_module_year, aggregate_year = _compute_rli(
        taxa_to_modules, year_taxa_statuses, DD_CATEGORIES, use_fixed_pool=False,
    )

    idx_to_label = {idx: label for label, idx in label_to_idx.items()}

    module_series = defaultdict(list)
    for (mod, idx), data in per_module_year.items():
        module_series[mod].append({
            'label': idx_to_label[idx],
            'value': data['rli'],
            'num_assessed': data['assessed'],
            'num_dd': data['dd'],
            'categories': data['categories'],
        })

    series = []
    for mod, points in module_series.items():
        if not any(p['categories'] for p in points):
            continue
        series.append({
            'name': mod,
            'points': sorted(points, key=lambda p: label_to_idx[p['label']]),
        })

    aggregate = sorted(
        [
            {
                'label': idx_to_label[idx],
                'value': data['rli'],
                'num_assessed': data['assessed'],
                'num_dd': data['dd'],
                'categories': data['categories'],
            }
            for idx, data in aggregate_year.items()
        ],
        key=lambda p: label_to_idx[p['label']],
    )

    search_process.set_status(SEARCH_FINISHED, False)
    search_process.save_to_file({'series': series, 'aggregate': aggregate})


# ---------------------------------------------------------------------------
# opensearch_spatial_dashboard_species_download
# ---------------------------------------------------------------------------

@shared_task(
    name='bims.tasks.opensearch_spatial_dashboard_species_download',
    queue='search',
)
def opensearch_spatial_dashboard_species_download(
    search_parameters=None, search_process_id=None
):
    import csv
    from django.db.models import Q
    from bims.models import SearchProcess
    from bims.models.search_process import SEARCH_PROCESSING, SEARCH_FINISHED
    from bims.models.taxonomy import Taxonomy
    from bims.models.iucn_status import IUCNStatus
    from bims.models.location_context import LocationContext
    from bims.models.location_context_group import LocationContextGroup
    from bims.views.download_csv_taxa_list import is_sanparks_project
    from bims.serializers.bio_collection_serializer import SANPARK_PARK_NAME
    from bims.opensearch.client import get_client
    from bims.opensearch.indices import COLLECTIONS_INDEX

    PARK_GROUP_KEYS = {
        'park_or_mpa_name', 'park_or_mpa',
        'parks_and_mpas', 'sanparks_and_mpas',
        'sanparks_mpas', 'parks_mpas',
    }

    if search_parameters is None:
        search_parameters = {}

    try:
        search_process = SearchProcess.objects.get(id=search_process_id)
    except SearchProcess.DoesNotExist:
        return

    search_process.set_status(SEARCH_PROCESSING)

    filter_clauses = _get_filter_clauses(search_parameters, search_process)
    client = get_client()

    response = _run_search(
        client, COLLECTIONS_INDEX, filter_clauses,
        aggs={
            'unique_taxa': {'terms': {'field': 'taxonomy_id', 'size': 50000}},
            'unique_sites': {'terms': {'field': 'site_id', 'size': 100000}},
        },
    )

    agg_data = response.get('aggregations', {})
    taxa_ids = [b['key'] for b in agg_data.get('unique_taxa', {}).get('buckets', [])]
    site_ids = [b['key'] for b in agg_data.get('unique_sites', {}).get('buckets', [])]

    park_group = LocationContextGroup.objects.filter(
        Q(key__in=list(PARK_GROUP_KEYS)) | Q(name__iexact=SANPARK_PARK_NAME)
    ).first()

    taxon_parks = {}
    if park_group and site_ids:
        site_park = {}
        for lc in LocationContext.objects.filter(
            site_id__in=site_ids, group=park_group
        ).values('site_id', 'value'):
            val = (lc['value'] or '').strip()
            if val:
                site_park[lc['site_id']] = val

        # Map taxonomy_id -> parks via location_context_values in OS
        # We need to know which site each taxon appears at. Use a smaller
        # site-level agg per taxon to build the mapping.
        taxon_site_response = _run_search(
            client, COLLECTIONS_INDEX, filter_clauses,
            aggs={
                'by_taxon': {
                    'terms': {'field': 'taxonomy_id', 'size': 50000},
                    'aggs': {
                        'by_site': {'terms': {'field': 'site_id', 'size': 1000}},
                    },
                }
            },
        )
        for t_bucket in (
            taxon_site_response.get('aggregations', {})
            .get('by_taxon', {})
            .get('buckets', [])
        ):
            tid = t_bucket['key']
            for s_bucket in t_bucket.get('by_site', {}).get('buckets', []):
                park = site_park.get(s_bucket['key'], '')
                if park:
                    taxon_parks.setdefault(tid, set()).add(park)
    elif site_ids:
        # No park group - use site names from OS location_context_values
        # or just leave taxon_parks empty; site names will be looked up below
        pass

    category_labels = dict(IUCNStatus.CATEGORY_CHOICES)

    taxa = Taxonomy.objects.filter(
        id__in=taxa_ids
    ).select_related('iucn_status').order_by('canonical_name')

    location_col = 'Park Name' if is_sanparks_project() else 'Site Name'
    csv_path = search_process.file_path + '.csv'
    headers = ['Scientific Name', location_col, 'Conservation Status Global']

    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        for taxon in taxa:
            iucn_global = ''
            if taxon.iucn_status:
                iucn_global = category_labels.get(
                    taxon.iucn_status.category, taxon.iucn_status.category
                )
            writer.writerow({
                'Scientific Name': taxon.canonical_name or '',
                location_col: ', '.join(sorted(taxon_parks.get(taxon.id, set()))),
                'Conservation Status Global': iucn_global,
            })

    if search_process.requester:
        from bims.tasks.email_csv import send_csv_via_email
        download_request_id = search_parameters.get('downloadRequestId')
        send_csv_via_email.delay(
            user_id=search_process.requester.id,
            csv_file=csv_path,
            file_name='species-list',
            download_request_id=download_request_id,
        )

    search_process.set_status(SEARCH_FINISHED, False)
    search_process.save_to_file({'status': SEARCH_FINISHED})
