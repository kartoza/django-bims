# coding=utf-8
import csv
import logging
from celery import shared_task
from hashlib import md5

logger = logging.getLogger(__name__)


@shared_task(name='bims.tasks.download_chemical_data_to_csv', queue='update')
def download_chemical_data_to_csv(path_file, site_id):
    from bims.models.chemical_record import ChemicalRecord
    from bims.serializers.chemical_records_serializer import (
        ChemicalRecordsOneRowSerializer)
    from bims.utils.celery import memcache_lock

    path_file_hexdigest = md5(path_file).hexdigest()

    lock_id = '{}-lock-{}'.format(
        download_chemical_data_to_csv.name,
        path_file_hexdigest
    )

    oid = '{0}'.format(path_file_hexdigest)

    with memcache_lock(lock_id, oid) as acquired:
        if acquired:
            queryset = ChemicalRecord.objects.filter(location_site_id=site_id)
            serializer = ChemicalRecordsOneRowSerializer(
                queryset,
                many=True
            )
            headers = serializer.data[0].keys()
            rows = serializer.data

            formatted_headers = []
            # Rename headers
            for header in headers:
                if header == 'class_name':
                    header = 'class'
                header = header.replace('_or_', '/')
                header = header.replace('_', ' ').capitalize()
                formatted_headers.append(header)

            with open(path_file, 'wb') as csv_file:
                writer = csv.DictWriter(csv_file, fieldnames=formatted_headers)
                writer.writeheader()
                writer.fieldnames = headers
                for row in rows:
                    writer.writerow(row)

            return

    logger.info(
        'Csv %s is already being processed by another worker',
        path_file)
