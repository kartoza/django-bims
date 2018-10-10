import os
import json
import logging
from celery import shared_task
from django.core.paginator import Paginator

logger = logging.getLogger(__name__)


def combine_results(new_results, old_results):
    for new_result in new_results:
        exists = False
        for old_result in old_results:
            if old_result['id'] == new_result['id']:
                old_result['count'] += new_result['count']
                exists = True
                continue
        if not exists:
            old_results.append(new_result)
    return old_results


@shared_task(name='bims.tasks.search_collection', queue='update')
def search_collection(query_value, filters, path_file, process):
    from bims.utils.celery import memcache_lock
    from bims.api_views.collection import GetCollectionAbstract
    from bims.api_views.search import SearchObjects
    from bims.models.search_process import SearchProcess

    lock_id = '{0}-lock-{1}'.format(
            path_file,
            process
    )

    oid = '{0}'.format(process)

    category = 'search_results'
    processing_label = 'processing'
    finished_label = 'finish'
    max_result = 100

    with memcache_lock(lock_id, oid) as acquired:
        if acquired:

            collection_results, \
            site_results, \
            fuzzy_search = GetCollectionAbstract.apply_filter(
                    query_value,
                    filters,
                    ignore_bbox=True)

            search_process, created = SearchProcess.objects.get_or_create(
                    category=category,
                    process_id=process
            )

            with open(path_file, 'wb') as status_file:
                status_file.write(json.dumps({
                    'status': processing_label,
                    'process': process
                }))
                search_process.file_path = path_file
                search_process.save()

            paginator = Paginator(collection_results, max_result)

            all_record_results = []
            all_site_results = []
            search_results = dict()
            search_results['status'] = {
                'status': processing_label,
                'process': process
            }

            for num_page in range(1, paginator.num_pages):
                page = paginator.page(num_page)
                if not page.object_list:
                    break
                collection_result = page.object_list
                record_results, site_results = \
                    SearchObjects.process_search(
                        collection_result, query_value)

                search_results['fuzzy_search'] = fuzzy_search

                if not all_record_results and not all_site_results:
                    all_record_results = record_results
                    all_site_results = site_results
                else:
                    # combine
                    all_record_results = combine_results(
                            new_results=record_results,
                            old_results=all_record_results
                    )

                search_results['records'] = all_record_results
                search_results['sites'] = all_site_results
                with open(path_file, 'wb') as result_file:
                    result_file.write(
                            json.dumps(search_results)
                    )

            if search_results:
                search_results['status'] = {
                    'status': finished_label
                }
                search_process.finished = True
                search_process.save()
                with open(path_file, 'wb') as result_file:
                    result_file.write(
                            json.dumps(search_results)
                    )

            return

    logger.info(
        'Search %s is already being processed by another worker',
        process)
