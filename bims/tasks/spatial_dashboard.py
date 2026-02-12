# coding=utf-8
import logging

from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(name='bims.tasks.spatial_dashboard_cons_status', queue='search')
def spatial_dashboard_cons_status(search_parameters=None, search_process_id=None):
    from bims.utils.celery import memcache_lock
    from bims.api_views.location_site_overview import LocationSiteOverviewData
    from bims.models.search_process import (
        SearchProcess,
        SEARCH_PROCESSING,
        SEARCH_FINISHED
    )

    if search_parameters is None:
        search_parameters = {}

    try:
        search_process = SearchProcess.objects.get(id=search_process_id)
    except SearchProcess.DoesNotExist:
        return

    lock_id = '{0}-lock-{1}'.format(
        search_process.file_path,
        search_process.process_id
    )
    oid = '{0}'.format(search_process.process_id)
    with memcache_lock(lock_id, oid) as acquired:
        if acquired:
            search_process.set_status(SEARCH_PROCESSING)

            overview_data = LocationSiteOverviewData()
            if search_process.requester and 'requester' not in search_parameters:
                search_parameters['requester'] = search_process.requester.id
            overview_data.search_filters = search_parameters

            biodiversity_data = overview_data.biodiversity_data() or {}
            modules = []
            for module_name, module_data in biodiversity_data.items():
                cons_status = module_data.get(
                    LocationSiteOverviewData.GROUP_CONS_STATUS, []
                )
                cleaned = []
                for item in cons_status:
                    cleaned.append({
                        'name': item.get('name') or item.get('iucn_category'),
                        'count': item.get('count', 0),
                        'colour': item.get('colour'),
                        'category': item.get('iucn_category'),
                    })
                modules.append({
                    'name': module_name,
                    'cons_status': cleaned
                })

            results = {
                'modules': modules
            }
            search_process.set_status(SEARCH_FINISHED, False)
            search_process.save_to_file(results)
            return
    logger.info(
        'Search %s is already being processed by another worker',
        search_process.process_id
    )


@shared_task(name='bims.tasks.spatial_dashboard_rli', queue='search')
def spatial_dashboard_rli(search_parameters=None, search_process_id=None):
    from django.db.models import Case, When, Value, F, Count, IntegerField
    from django.db.models.functions import ExtractYear
    from bims.utils.celery import memcache_lock
    from bims.api_views.search import CollectionSearch
    from bims.models.search_process import (
        SearchProcess,
        SEARCH_PROCESSING,
        SEARCH_FINISHED
    )

    if search_parameters is None:
        search_parameters = {}

    try:
        search_process = SearchProcess.objects.get(id=search_process_id)
    except SearchProcess.DoesNotExist:
        return

    lock_id = '{0}-lock-{1}'.format(
        search_process.file_path,
        search_process.process_id
    )
    oid = '{0}'.format(search_process.process_id)
    with memcache_lock(lock_id, oid) as acquired:
        if acquired:
            search_process.set_status(SEARCH_PROCESSING)

            if search_process.requester and 'requester' not in search_parameters:
                search_parameters['requester'] = search_process.requester.id

            search = CollectionSearch(search_parameters)
            collection_results = search.process_search()

            counts = collection_results.annotate(
                year=ExtractYear('collection_date'),
                module_name=F('module_group__name'),
                iucn=Case(
                    When(taxonomy__iucn_status__category__isnull=False,
                         then=F('taxonomy__iucn_status__category')),
                    default=Value('NE')
                ),
                weight=Case(
                    When(taxonomy__iucn_status__category='LC', then=Value(0)),
                    When(taxonomy__iucn_status__category='NT', then=Value(1)),
                    When(taxonomy__iucn_status__category='VU', then=Value(2)),
                    When(taxonomy__iucn_status__category='EN', then=Value(3)),
                    When(taxonomy__iucn_status__category='CR', then=Value(4)),
                    When(taxonomy__iucn_status__category='EX', then=Value(5)),
                    When(taxonomy__iucn_status__category='EW', then=Value(5)),
                    default=Value(0),
                    output_field=IntegerField()
                )
            ).values(
                'year', 'module_name', 'iucn', 'weight'
            ).annotate(
                count=Count('id')
            ).values(
                'year', 'module_name', 'iucn', 'weight', 'count'
            )

            per_module_year = {}
            aggregate_year = {}
            for row in counts:
                year = row['year']
                module = row['module_name'] or 'Unknown'
                iucn = row['iucn']
                weight = row['weight'] or 0
                count = row['count'] or 0

                if year is None:
                    continue

                key = (module, year)
                if key not in per_module_year:
                    per_module_year[key] = {
                        'total': 0,
                        'weighted': 0
                    }

                if iucn != 'DD':
                    per_module_year[key]['total'] += count
                    per_module_year[key]['weighted'] += (weight * count)

                if year not in aggregate_year:
                    aggregate_year[year] = {
                        'total': 0,
                        'weighted': 0
                    }
                if iucn != 'DD':
                    aggregate_year[year]['total'] += count
                    aggregate_year[year]['weighted'] += (weight * count)

            module_series = {}
            for (module, year), values in per_module_year.items():
                total = values['total']
                if total <= 0:
                    continue
                rli = 1 - (values['weighted'] / float(total * 5))
                module_series.setdefault(module, []).append({
                    'year': int(year),
                    'value': round(rli, 4)
                })

            series = []
            for module, points in module_series.items():
                series.append({
                    'name': module,
                    'points': sorted(points, key=lambda x: x['year'])
                })

            aggregate = []
            for year, values in aggregate_year.items():
                total = values['total']
                if total <= 0:
                    continue
                rli = 1 - (values['weighted'] / float(total * 5))
                aggregate.append({
                    'year': int(year),
                    'value': round(rli, 4)
                })
            aggregate = sorted(aggregate, key=lambda x: x['year'])

            results = {
                'series': series,
                'aggregate': aggregate
            }
            search_process.set_status(SEARCH_FINISHED, False)
            search_process.save_to_file(results)
            return
    logger.info(
        'Search %s is already being processed by another worker',
        search_process.process_id
    )


@shared_task(name='bims.tasks.spatial_dashboard_map', queue='search')
def spatial_dashboard_map(search_parameters=None, search_process_id=None):
    from bims.utils.celery import memcache_lock
    from bims.api_views.search import CollectionSearch
    from bims.models.search_process import (
        SearchProcess,
        SEARCH_PROCESSING,
        SEARCH_FINISHED
    )

    if search_parameters is None:
        search_parameters = {}

    try:
        search_process = SearchProcess.objects.get(id=search_process_id)
    except SearchProcess.DoesNotExist:
        return

    lock_id = '{0}-lock-{1}'.format(
        search_process.file_path,
        search_process.process_id
    )
    oid = '{0}'.format(search_process.process_id)
    with memcache_lock(lock_id, oid) as acquired:
        if acquired:
            search_process.set_status(SEARCH_PROCESSING)

            if search_process.requester and 'requester' not in search_parameters:
                search_parameters['requester'] = search_process.requester.id

            search = CollectionSearch(search_parameters)
            search.process_search()

            if search.location_sites_raw_query:
                search_process.set_search_raw_query(
                    search.location_sites_raw_query
                )
                search_process.create_view()
                view_name = search_process.process_id
            else:
                view_name = None

            results = {
                'extent': search.extent(),
                'sites_raw_query': view_name
            }
            search_process.set_status(SEARCH_FINISHED, False)
            search_process.save_to_file(results)
            return
    logger.info(
        'Search %s is already being processed by another worker',
        search_process.process_id
    )


@shared_task(name='bims.tasks.spatial_dashboard_summary', queue='search')
def spatial_dashboard_summary(search_parameters=None, search_process_id=None):
    from django.db.models import Case, When, Value, F, Count, CharField
    from bims.models import TaxonGroup, IUCNStatus
    from bims.utils.celery import memcache_lock
    from bims.api_views.search import CollectionSearch
    from bims.models.search_process import (
        SearchProcess,
        SEARCH_PROCESSING,
        SEARCH_FINISHED
    )

    if search_parameters is None:
        search_parameters = {}

    try:
        search_process = SearchProcess.objects.get(id=search_process_id)
    except SearchProcess.DoesNotExist:
        return

    lock_id = '{0}-lock-{1}'.format(
        search_process.file_path,
        search_process.process_id
    )
    oid = '{0}'.format(search_process.process_id)
    with memcache_lock(lock_id, oid) as acquired:
        if acquired:
            search_process.set_status(SEARCH_PROCESSING)

            if search_process.requester and 'requester' not in search_parameters:
                search_parameters['requester'] = search_process.requester.id

            search = CollectionSearch(search_parameters)
            collection_results = search.process_search()

            modules_qs = TaxonGroup.objects.filter(
                category='SPECIES_MODULE'
            ).order_by('display_order')
            module_names = list(modules_qs.values_list('name', flat=True))

            module_field = Case(
                When(module_group__name__isnull=True, then=Value('Unknown')),
                default=F('module_group__name'),
                output_field=CharField()
            )

            number_of_taxa = collection_results.annotate(
                module_name=module_field
            ).values(
                'module_name'
            ).annotate(
                count=Count('taxonomy_id', distinct=True)
            ).values('module_name', 'count')

            origin_field = Case(
                When(taxonomy__origin='', then=Value('Unknown')),
                When(taxonomy__origin__icontains='unknown', then=Value('Unknown')),
                default=F('taxonomy__origin'),
                output_field=CharField()
            )

            origin_counts = collection_results.annotate(
                module_name=module_field,
                origin_name=origin_field
            ).values(
                'module_name', 'origin_name'
            ).annotate(
                count=Count('taxonomy_id', distinct=True)
            ).values('module_name', 'origin_name', 'count')

            endemism_field = Case(
                When(taxonomy__endemism__name__isnull=True, then=Value('Unknown')),
                default=F('taxonomy__endemism__name'),
                output_field=CharField()
            )
            endemism_counts = collection_results.annotate(
                module_name=module_field,
                endemism_name=endemism_field
            ).values(
                'module_name', 'endemism_name'
            ).annotate(
                count=Count('taxonomy_id', distinct=True)
            ).values('module_name', 'endemism_name', 'count')

            iucn_labels = dict(IUCNStatus.CATEGORY_CHOICES)

            global_cons_counts = collection_results.filter(
                taxonomy__iucn_status__national=False
            ).annotate(
                module_name=module_field,
                cons_name=Case(
                    When(taxonomy__iucn_status__category__isnull=True, then=Value('NE')),
                    default=F('taxonomy__iucn_status__category'),
                    output_field=CharField()
                )
            ).values(
                'module_name', 'cons_name'
            ).annotate(
                count=Count('taxonomy_id', distinct=True)
            ).values('module_name', 'cons_name', 'count')

            national_cons_counts = collection_results.filter(
                taxonomy__iucn_status__national=True
            ).annotate(
                module_name=module_field,
                cons_name=Case(
                    When(taxonomy__iucn_status__category__isnull=True, then=Value('NE')),
                    default=F('taxonomy__iucn_status__category'),
                    output_field=CharField()
                )
            ).values(
                'module_name', 'cons_name'
            ).annotate(
                count=Count('taxonomy_id', distinct=True)
            ).values('module_name', 'cons_name', 'count')

            def rows_from_counts(rows, label_key, label_map=None):
                matrix = {}
                for row in rows:
                    raw_label = row[label_key] or 'Unknown'
                    if label_map and raw_label in label_map:
                        label = label_map[raw_label]
                    else:
                        label = raw_label
                    module = row['module_name'] or 'Unknown'
                    matrix.setdefault(label, {})
                    matrix[label][module] = row['count']
                return matrix

            summary = {
                'modules': module_names,
                'overview': {
                    'Number of Taxa': {
                        row['module_name']: row['count'] for row in number_of_taxa
                    }
                },
                'origin': rows_from_counts(origin_counts, 'origin_name'),
                'endemism': rows_from_counts(endemism_counts, 'endemism_name'),
                'cons_status_global': rows_from_counts(global_cons_counts, 'cons_name', iucn_labels),
                'cons_status_national': rows_from_counts(national_cons_counts, 'cons_name', iucn_labels)
            }

            for section_key in ['overview', 'origin', 'endemism', 'cons_status_global', 'cons_status_national']:
                section = summary.get(section_key, {})
                if isinstance(section, dict):
                    for row_key, values in section.items():
                        if isinstance(values, dict):
                            for module in module_names:
                                values.setdefault(module, 0)

            results = summary
            search_process.set_status(SEARCH_FINISHED, False)
            search_process.save_to_file(results)
            return
    logger.info(
        'Search %s is already being processed by another worker',
        search_process.process_id
    )
