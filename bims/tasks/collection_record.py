import csv
import sys
import logging
from celery import shared_task
from django.core.management import call_command


logger = logging.getLogger(__name__)
IN_CELERY_WORKER_PROCESS = (
       False
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
