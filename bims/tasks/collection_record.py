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


@shared_task(name='bims.tasks.resume_stalled_downloads', queue='update')
def resume_stalled_downloads():
    """
    Periodic task: find occurrence download requests whose progress has not
    advanced for STALE_THRESHOLD_MINUTES and restart them from scratch.
    """
    from datetime import timedelta
    from django.utils import timezone
    from bims.models.download_request import DownloadRequest
    from bims.download.csv_download import STALE_THRESHOLD_MINUTES

    stale_cutoff = timezone.now() - timedelta(minutes=STALE_THRESHOLD_MINUTES)

    stalled = DownloadRequest.objects.filter(
        resource_name='Occurrence Data',
        resource_type__in=['CSV', 'XLS'],
        approved=True,
        rejected=False,
        request_file='',
        progress__isnull=False,
        progress_updated_at__lt=stale_cutoff,
        download_path__isnull=False,
        download_params__isnull=False,
    )

    for dr in stalled:
        logger.info(
            'Resuming stalled download request %d (last update: %s)',
            dr.id, dr.progress_updated_at
        )
        path_file = dr.download_path
        request_params = dr.download_params or {}

        # Remove the partial file so the task starts clean
        try:
            import os
            if path_file and os.path.exists(path_file):
                os.remove(path_file)
        except OSError as exc:
            logger.warning('Could not remove partial file %s: %s', path_file, exc)

        dr.progress = None
        dr.progress_updated_at = None
        dr.save(update_fields=['progress', 'progress_updated_at'])

        download_collection_record_task.delay(
            path_file,
            request_params,
            send_email=True,
            user_id=dr.requester_id,
        )


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
