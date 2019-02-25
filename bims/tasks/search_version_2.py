import logging
from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(name='bims.tasks.search_task', queue='update')
def search_task(parameters, search_process_id):
    from bims.utils.celery import memcache_lock
    from bims.api_views.search_version_2 import SearchVersion2
    from bims.models.search_process import (
        SearchProcess,
        SEARCH_PROCESSING,
        SEARCH_FINISHED,
        SEARCH_FAILED
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

            search = SearchVersion2(parameters)
            search_results = search.get_summary_data()
            if search_results:
                search_process.set_search_raw_query(
                    search.location_sites_raw_query
                )
                search_process.create_view()
                search_process.set_status(SEARCH_FINISHED, False)
                search_results['status'] = SEARCH_FINISHED
                search_process.save_to_file(search_results)
            else:
                search_process.set_status(SEARCH_FAILED)
            return


    logger.info(
        'Search %s is already being processed by another worker',
        search_process.process_id)
