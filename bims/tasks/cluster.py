from celery import shared_task
import json
import logging

from django.core.paginator import Paginator

logger = logging.getLogger(__name__)


@shared_task(name='bims.tasks.generate_search_cluster', queue='update')
def generate_search_cluster(query_value,
                            filters,
                            filename,
                            path_file):
    from bims.api_views.collection import GetCollectionAbstract
    from bims.utils.celery import memcache_lock
    from bims.models.search_process import SearchProcess

    lock_id = '{0}-lock-{1}'.format(
            path_file,
            filename
    )

    oid = '{0}'.format(filename)

    with memcache_lock(lock_id, oid) as acquired:
        if acquired:
            collection_results, \
                site_results, \
                fuzzy_search = GetCollectionAbstract.apply_filter(
                    query_value,
                    filters,
                    ignore_bbox=True)
            search_process, created = SearchProcess.objects.get_or_create(
                    category='cluster_generation',
                    process_id=filename
            )
            status = {
                'current_status': 'processing',
                'process': filename
            }
            with open(path_file, 'wb') as status_file:
                status_file.write(json.dumps({
                    'status': status
                }))
                search_process.file_path = path_file
                search_process.save()

            collection_sites = list(
                    collection_results.values(
                            'location_site_id',
                            'location_coordinates',
                            'location_site_name'))
            collection_distinct = {}
            all_sites = []

            paginator = Paginator(collection_sites, 100)
            response_data = dict()
            response_data['status'] = status
            response_data['data'] = []

            # Get location site distinct values
            for num_page in range(1, paginator.num_pages + 1):
                object_list = paginator.page(num_page).object_list
                for site in object_list:
                    location_site_id = int(site['location_site_id'])
                    if location_site_id not in collection_distinct:
                        collection_distinct[location_site_id] = site
                        all_sites.append(site)

                response_data['data'] = all_sites
                with open(path_file, 'wb') as cluster_file:
                    cluster_file.write(json.dumps(response_data))

            response_data['status']['current_status'] = 'finish'
            search_process.finished = True
            search_process.save()
            with open(path_file, 'wb') as cluster_file:
                cluster_file.write(json.dumps(response_data))

            return

    logger.info(
            'Cluster search %s is already being processed by another worker',
            path_file)
