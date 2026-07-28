import csv
import os
import logging
from celery import shared_task

logger = logging.getLogger('bims')


@shared_task(name='bims.tasks.download_duplicated_records_to_csv', queue='update')
def download_duplicated_records_to_csv(download_request_id):
    """Write duplicate records to a CSV and attach it to a DownloadRequest.

    Progress is reported on the DownloadRequest so admins can follow it and
    download the finished file from the Download Requests page.
    """
    from django.conf import settings
    from django.utils import timezone
    from bims.models import BiologicalCollectionRecord
    from bims.models.download_request import DownloadRequest
    from bims.serializers.bio_collection_serializer import (
        BioCollectionOneRowSerializer
    )
    from bims.utils.celery import memcache_lock
    from bims.helpers.get_duplicates import get_duplicate_records
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
    filename = 'duplicate_records_{}.csv'.format(timezone.now().date())
    path_file = os.path.join(path_folder, filename)

    lock_id = '{0}-lock-{1}'.format(
        download_duplicated_records_to_csv.name,
        path_file
    )
    oid = '{0}'.format(download_request_id)

    with memcache_lock(lock_id, oid) as acquired:
        if not acquired:
            logger.info(
                'Csv %s is already being processed by another worker',
                path_file)
            return

        duplicate_groups = list(get_duplicate_records())
        total = len(duplicate_groups)

        rows = []
        headers = []
        for index, value in enumerate(duplicate_groups, start=1):
            value = dict(value)
            value.pop('duplicate', None)
            records = BiologicalCollectionRecord.objects.filter(**value)
            serializer = BioCollectionOneRowSerializer(
                records,
                many=True,
                context={'show_link': True}
            )
            # Collect the union of keys across every row: different groups can
            # produce different columns (e.g. optional fields).
            for record_row in serializer.data:
                for key in record_row.keys():
                    if key not in headers:
                        headers.append(key)
            rows += list(serializer.data)

            # Report progress periodically (and on the final group).
            if index % 10 == 0 or index == total:
                download_request.progress = '{}/{}'.format(index, total)
                download_request.progress_updated_at = timezone.now()
                download_request.save(
                    update_fields=['progress', 'progress_updated_at'])

        # Rename headers for readability.
        formatted_headers = []
        for header in headers:
            if header == 'class_name':
                header = 'class'
            header = header.replace('_or_', '/')
            header = header.replace('_', ' ').capitalize()
            formatted_headers.append(header)

        with open(path_file, 'w') as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=formatted_headers)
            writer.writeheader()
            writer.fieldnames = headers
            for row in rows:
                writer.writerow(row)

        # Attach the finished file to the download request.
        download_request.request_category = 'Duplicate Records'
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
                file_name='Duplicate Records',
                approved=True,
                download_request_id=download_request.id
            )
