import csv
import os
import logging
from celery import shared_task

logger = logging.getLogger('bims')

CSV_HEADERS = [
    'ID', 'Site code', 'Legacy site code', 'Name', 'Latitude', 'Longitude',
    'River', 'Wetland name', 'Ecosystem type', 'Description', 'Owner',
    'Validated', 'Date created', 'URL',
]


@shared_task(name='bims.tasks.download_duplicated_sites_to_csv', queue='update')
def download_duplicated_sites_to_csv(download_request_id):
    """Write duplicate location sites to a CSV and attach it to a DownloadRequest.

    Progress is reported on the DownloadRequest so admins can follow it and
    download the finished file from the Download Requests page.
    """
    from django.conf import settings
    from django.utils import timezone
    from bims.models.download_request import DownloadRequest
    from bims.utils.celery import memcache_lock
    from bims.helpers.get_duplicates import get_duplicate_sites
    from bims.utils.domain import get_current_domain
    from bims.tasks import send_csv_via_email

    try:
        download_request = DownloadRequest.objects.get(id=download_request_id)
    except DownloadRequest.DoesNotExist:
        logger.error('DownloadRequest %s not found', download_request_id)
        return

    username = (
        download_request.requester.username
        if download_request.requester else 'admin'
    )
    path_folder = os.path.join(
        settings.MEDIA_ROOT, settings.PROCESSED_CSV_PATH, username
    )
    os.makedirs(path_folder, exist_ok=True)
    filename = 'duplicate_sites_{}.csv'.format(timezone.now().date())
    path_file = os.path.join(path_folder, filename)

    lock_id = '{0}-lock-{1}'.format(
        download_duplicated_sites_to_csv.name,
        path_file
    )
    oid = '{0}'.format(download_request_id)

    with memcache_lock(lock_id, oid) as acquired:
        if not acquired:
            logger.info(
                'Csv %s is already being processed by another worker',
                path_file)
            return

        sites = get_duplicate_sites().select_related('river', 'owner')
        total = sites.count()
        current_domain = get_current_domain()

        with open(path_file, 'w', newline='') as csv_file:
            writer = csv.writer(csv_file)
            writer.writerow(CSV_HEADERS)
            for index, site in enumerate(
                    sites.iterator(chunk_size=500), start=1):
                writer.writerow([
                    site.id,
                    site.site_code,
                    site.legacy_site_code,
                    site.name,
                    site.latitude,
                    site.longitude,
                    site.river.name if site.river else '',
                    site.wetland_name,
                    site.ecosystem_type,
                    site.site_description,
                    site.owner.username if site.owner else '',
                    'Yes' if site.validated else 'No',
                    site.date_created.strftime('%Y-%m-%d')
                    if site.date_created else '',
                    'http://{domain}/location-site-form/update/?id={id}'.format(
                        domain=current_domain, id=site.id
                    ),
                ])

                # Report progress periodically (and on the final row).
                if index % 20 == 0 or index == total:
                    download_request.progress = '{}/{}'.format(index, total)
                    download_request.progress_updated_at = timezone.now()
                    download_request.save(
                        update_fields=['progress', 'progress_updated_at'])

        # Attach the finished file to the download request.
        download_request.request_category = 'Duplicate Sites'
        download_request.request_file = path_file
        download_request.progress = '{}/{}'.format(total, total)
        download_request.progress_updated_at = timezone.now()
        download_request.processing = False
        download_request.save(update_fields=[
            'request_category', 'request_file', 'progress',
            'progress_updated_at', 'processing'
        ])

        # Notify the requester by email as well.
        if download_request.requester:
            send_csv_via_email(
                user_id=download_request.requester.id,
                csv_file=path_file,
                file_name='Duplicate Sites',
                approved=True,
                download_request_id=download_request.id
            )
