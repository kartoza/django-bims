import csv
import sys
import logging
from celery import shared_task
from django.core.management import call_command


logger = logging.getLogger(__name__)
IN_CELERY_WORKER_PROCESS = (
        sys.argv and sys.argv[0].endswith('celery') and 'worker' in sys.argv
)


@shared_task(name='bims.tasks.update_search_index', queue='update')
def update_search_index():
    call_command('rebuild_index', verbosity=0, interactive=False)


@shared_task(name='bims.tasks.update_cluster', queue='update')
def update_cluster(ids=None):
    from bims.models.boundary_type import BoundaryType
    from bims.models.boundary import Boundary
    if not ids:
        for boundary_type in BoundaryType.objects.all().order_by('-level'):
            for boundary in Boundary.objects.filter(type=boundary_type):
                print('generate cluster for %s' % boundary)
                boundary.generate_cluster()
    else:
        for boundary in Boundary.objects.filter(
                id__in=ids).order_by('-type__level'):
            while True:
                print('generate cluster for %s' % boundary)
                boundary.generate_cluster()
                boundary = boundary.top_level_boundary
                if not boundary:
                    break


@shared_task(name='bims.tasks.download_collection_record_task', queue='update')
def download_collection_record_task(
        path_file, request, send_email=False, user_id=None):
    from bims.utils.celery import memcache_lock
    from bims.download.collection_record import download_collection_records

    if IN_CELERY_WORKER_PROCESS:
        lock_id = '{0}-lock-{1}'.format(
            download_collection_record_task.name,
            path_file
        )

        oid = '{0}'.format(path_file)
        with memcache_lock(lock_id, oid) as acquired:
            if acquired:
                return download_collection_records(
                    path_file, request, send_email, user_id
                )
        logger.info(
            'Csv %s is already being processed by another worker',
            path_file)
    else:
        return download_collection_records(
            path_file, request, send_email, user_id
        )

    logger.info(
        'Csv %s is already being processed by another worker',
        path_file)


@shared_task(name='bims.tasks.download_gbif_ids', queue='update')
def download_gbif_ids(path_file, request, send_email=False, user_id=None):
    from bims.utils.celery import memcache_lock
    from bims.api_views.location_site import generate_gbif_ids_data

    if IN_CELERY_WORKER_PROCESS:
        lock_id = '{0}-lock-{1}'.format(
            download_gbif_ids.name,
            path_file
        )

        oid = '{0}'.format(path_file)
        with memcache_lock(lock_id, oid) as acquired:
            if acquired:
                return generate_gbif_ids_data(
                    path_file, request, send_email, user_id
                )
        logger.info(
            'Csv %s is already being processed by another worker',
            path_file)
    else:
        return generate_gbif_ids_data(
            path_file, request, send_email, user_id
        )

    logger.info(
        'Csv %s is already being processed by another worker',
        path_file)


@shared_task(
    name='bims.tasks.assign_site_to_uncategorized_records',
    queue='update')
def assign_site_to_uncategorized_records(module_group_id, site_id):
    """
    Asynchronously assigns a site to all biological collection records
    that belong to a specific module group but don't yet have a site assigned.
    """
    from bims.models.biological_collection_record import (
        BiologicalCollectionRecord
    )
    BiologicalCollectionRecord.objects.filter(
        module_group_id=module_group_id,
        source_site__isnull=True
    ).update(
        source_site_id=site_id
    )
