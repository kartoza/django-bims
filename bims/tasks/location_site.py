import logging
from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(name='bims.tasks.location_site_summary', queue='update')
def location_site_summary(parameters, search_process_id):
    from bims.utils.celery import memcache_lock
    from bims.api_views.location_site import LocationSiteSummaryGenerator
    from bims.models.search_process import (
        SearchProcess,
        SEARCH_PROCESSING,
    )
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

            summary_generator = LocationSiteSummaryGenerator()
            summary_generator.generate(
                filters=parameters,
                process_id=search_process_id
            )

    logger.info(
        'Search %s is already being processed by another worker',
        search_process.process_id)
