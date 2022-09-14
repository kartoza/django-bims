# coding=utf-8
import logging
from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(name='bims.tasks.location_sites_overview', queue='search')
def location_sites_overview(
        search_parameters=None,
        search_process_id=None
    ):
    from bims.utils.celery import memcache_lock
    from bims.api_views.location_site_overview import (
        LocationSiteOverviewData
    )
    from bims.models.search_process import (
        SearchProcess,
        SEARCH_PROCESSING,
        SEARCH_FINISHED
    )

    if search_parameters is None:
        search_parameters = {}

    try:
        search_process = SearchProcess.objects.get(
            id=search_process_id
        )
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
            overview_data.search_filters = search_parameters
            results = dict()
            results[LocationSiteOverviewData.BIODIVERSITY_DATA] = (
                overview_data.biodiversity_data()
            )
            results[LocationSiteOverviewData.SASS_EXIST] = (
                overview_data.is_sass_exist
            )
            search_process.set_status(SEARCH_FINISHED, False)
            search_process.save_to_file(results)
    logger.info(
        'Search %s is already being processed by another worker',
        search_process.process_id)


@shared_task(name='bims.tasks.update_location_context', queue='geocontext')
def update_location_context(location_site_id, generate_site_code=False):
    from bims.utils.logger import log
    from bims.models import LocationSite
    from bims.utils.location_context import get_location_context_data
    if isinstance(location_site_id, str):
        if ',' in location_site_id:
            get_location_context_data(
                site_id=str(location_site_id),
                only_empty=False,
                should_generate_site_code=generate_site_code
            )
            return
    try:
        LocationSite.objects.get(id=location_site_id)
    except LocationSite.DoesNotExist:
        log('Location site does not exist')
        return

    get_location_context_data(
        site_id=str(location_site_id),
        only_empty=False,
        should_generate_site_code=generate_site_code
    )
