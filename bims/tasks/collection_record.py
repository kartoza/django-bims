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


@shared_task(name='bims.tasks.resume_stalled_downloads', queue='update', ignore_result=True)
def resume_stalled_downloads():
    """
    Periodic task: find occurrence download requests whose progress has not
    advanced for STALE_THRESHOLD_MINUTES and restart them from scratch.
    Runs across all tenants.
    """
    import os
    from datetime import timedelta
    from django.utils import timezone
    from django_tenants.utils import get_tenant_model, tenant_context
    from bims.models.download_request import DownloadRequest, params_from_dashboard_url
    from bims.download.csv_download import STALE_THRESHOLD_MINUTES
    stale_cutoff = timezone.now() - timedelta(minutes=STALE_THRESHOLD_MINUTES)

    for tenant in get_tenant_model().objects.all():
        with tenant_context(tenant):
            stalled = DownloadRequest.objects.filter(
                resource_name='Occurrence Data',
                resource_type__in=['CSV', 'XLS'],
                approved=True,
                rejected=False,
                request_file='',
                progress_updated_at__lt=stale_cutoff,
                progress_updated_at__isnull=False,
            )

            for dr in stalled:
                path_file = dr.download_path
                request_params = dr.download_params

                if not path_file or not request_params:
                    path_file, request_params = params_from_dashboard_url(dr)
                    if not path_file or not request_params:
                        logger.warning(
                            '[%s] Skipping download request %d: '
                            'cannot resolve path/params',
                            tenant.schema_name, dr.id
                        )
                        continue
                    dr.download_path = path_file
                    dr.download_params = request_params
                    dr.save(update_fields=['download_path', 'download_params'])

                logger.info(
                    '[%s] Resuming stalled download request %d (last update: %s)',
                    tenant.schema_name, dr.id, dr.progress_updated_at
                )

                try:
                    if path_file and os.path.exists(path_file):
                        os.remove(path_file)
                except OSError as exc:
                    logger.warning(
                        '[%s] Could not remove partial file %s: %s',
                        tenant.schema_name, path_file, exc
                    )

                dr.progress = None
                dr.progress_updated_at = None
                dr.save(update_fields=['progress', 'progress_updated_at'])

                download_collection_record_task.delay(
                    path_file,
                    request_params,
                    send_email=True,
                    user_id=dr.requester_id,
                )


@shared_task(name='bims.tasks.cleanup_expired_download_files', queue='update', ignore_result=True)
def cleanup_expired_download_files():
    """
    Periodic task: delete download files for requests older than the configured
    expiry period (SiteSetting.download_request_expiry_months, default 2 months).
    Only the file is removed; the DownloadRequest record is kept.
    Runs across all tenants.
    """
    import os
    from dateutil.relativedelta import relativedelta
    from django.utils import timezone
    from django_tenants.utils import get_tenant_model, tenant_context
    from bims.models.download_request import DownloadRequest

    for tenant in get_tenant_model().objects.all():
        with tenant_context(tenant):
            from preferences import preferences
            months = getattr(preferences.SiteSetting, 'download_request_expiry_months', 2)
            if not months:
                # Infinite retention — nothing to clean up for this tenant.
                continue
            expiry_cutoff = timezone.now() - relativedelta(months=months)

            expired = DownloadRequest.objects.filter(
                request_date__lt=expiry_cutoff,
                request_file__isnull=False,
            ).exclude(request_file='')

            for dr in expired:
                file_path = None
                try:
                    file_path = dr.request_file.path
                except (ValueError, OSError):
                    pass

                if file_path and os.path.exists(file_path):
                    try:
                        os.remove(file_path)
                        logger.info(
                            '[%s] Deleted expired download file for request %d: %s',
                            tenant.schema_name, dr.id, file_path
                        )
                    except OSError as exc:
                        logger.warning(
                            '[%s] Could not delete expired file for request %d (%s): %s',
                            tenant.schema_name, dr.id, file_path, exc
                        )
                        continue

                dr.request_file = None
                dr.save(update_fields=['request_file'])


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
