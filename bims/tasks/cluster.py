from celery import shared_task
import json
import logging

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

            with open(path_file, 'wb') as status_file:
                status_file.write(json.dumps({
                    'status': 'processing',
                    'process': filename
                }))

            cluster = ClusterCollection.clustering_process(
                    collection_results,
                    site_results,
                    int(float(zoom)),
                    int(icon_pixel_x),
                    int(icon_pixel_y)
            )

            serializer = geo_serializer(cluster)['features']

            with open(path_file, 'wb') as cluster_file:
                cluster_file.write(json.dumps(serializer))

            return

    logger.info(
            'Cluster search %s is already being processed by another worker',
            path_file)
