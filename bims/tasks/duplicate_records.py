import csv
import os
import logging
from celery import shared_task

logger = logging.getLogger('bims')


@shared_task(name='bims.tasks.download_duplicated_records_to_csv', queue='update')
def download_duplicated_records_to_csv(path_file, user_email):
    from django.core.mail import send_mail
    from django.conf import settings
    from django.contrib.sites.models import Site
    from bims.models import BiologicalCollectionRecord
    from bims.serializers.bio_collection_serializer import BioCollectionOneRowSerializer
    from bims.utils.celery import memcache_lock
    from bims.helpers.get_duplicates import get_duplicate_records

    lock_id = '{0}-lock-{1}'.format(
        download_duplicated_records_to_csv.name,
        path_file
    )

    oid = '{0}'.format(path_file)

    with memcache_lock(lock_id, oid) as acquired:
        if acquired:
            rows = []
            headers = []
            queryset = list(get_duplicate_records())
            for value in queryset:
                del value['duplicate']
                records = BiologicalCollectionRecord.objects.filter(
                    **value
                )
                serializer = BioCollectionOneRowSerializer(
                    records,
                    many=True,
                    context={'show_link': True}
                )
                if len(serializer.data[0].keys()) > len(headers):
                    headers = serializer.data[0].keys()
                rows += list(serializer.data)

            formatted_headers = []
            # Rename headers
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

            send_mail(
                'Duplicate Records File Is Ready',
                'Dear Admin,\n\n'
                'File is ready to download:\n'
                'http://{site}{path}\n\n'
                'Sincerely,\nBIMS Team.'.format(
                    site=Site.objects.get_current().domain,
                    path=os.path.join(
                        settings.MEDIA_URL,
                        settings.PROCESSED_CSV_PATH,
                        path_file.split('/')[-1]
                    ),
                ),
                '{}'.format(settings.SERVER_EMAIL),
                [user_email],
                fail_silently=False
            )

            return

    logger.info(
        'Csv %s is already being processed by another worker',
        path_file)
