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
    from bims.models.download_request import DownloadRequest

    def _mark_failed(error_msg):
        """Mark download request as failed if it exists."""
        download_request_id = None
        if isinstance(request, dict):
            download_request_id = request.get('downloadRequestId')
        elif hasattr(request, 'get'):
            download_request_id = request.get('downloadRequestId')
        if download_request_id:
            try:
                dr = DownloadRequest.objects.get(id=download_request_id)
                dr.processing = False
                dr.progress = f"Error: {str(error_msg)[:200]}"
                dr.save()
            except (DownloadRequest.DoesNotExist, ValueError):
                pass

    def _run_download():
        try:
            return download_collection_records(
                path_file, request, send_email, user_id
            )
        except Exception as e:
            logger.error(f"Error downloading collection records: {e}")
            _mark_failed(e)
            raise

    if IN_CELERY_WORKER_PROCESS:
        lock_id = '{0}-lock-{1}'.format(
            download_collection_record_task.name,
            path_file
        )

        oid = '{0}'.format(path_file)
        with memcache_lock(lock_id, oid) as acquired:
            if acquired:
                return _run_download()
        logger.info(
            'Csv %s is already being processed by another worker',
            path_file)
    else:
        return _run_download()

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
