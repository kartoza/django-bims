from celery import shared_task
import json
import logging

from django.core.paginator import Paginator

logger = logging.getLogger(__name__)


@shared_task(name='bims.tasks.generate_search_cluster', queue='update')
def generate_search_cluster(zoom,
                            icon_pixel_x,
                            icon_pixel_y,
                            query_value,
                            filters,
                            filename,
                            path_file):
    from bims.api_views.collection import GetCollectionAbstract, \
        ClusterCollection
    from bims.utils.celery import memcache_lock
    from bims.utils.cluster_point import geo_serializer
    from bims.models.search_process import SearchProcess

    lock_id = '{0}-lock-{1}'.format(
            zoom,
            filename
    )

    oid = '{0}'.format(filename)

    with memcache_lock(lock_id, oid) as acquired:
        if acquired:
            collection_results, \
                site_results, \
                fuzzy_search = GetCollectionAbstract.apply_filter(
                    query_value,
                    filters)
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

            max_result = 100
            paginator = Paginator(collection_results, max_result)
            cluster_points = []
            sites = []
            response_data = dict()
            response_data['status'] = status

            for num_page in range(1, paginator.num_pages + 1):
                page = paginator.page(num_page)
                if not page.object_list:
                    break
                cluster_points, sites = ClusterCollection.clustering_process(
                        page.object_list,
                        site_results,
                        int(float(zoom)),
                        int(icon_pixel_x),
                        int(icon_pixel_y),
                        cluster_points,
                        sites
                )

                serializer = geo_serializer(cluster_points)['features']
                response_data['data'] = serializer

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
