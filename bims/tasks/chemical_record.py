# coding=utf-8
import csv
import logging
from celery import shared_task
from hashlib import sha256
from django.db.models import Q

logger = logging.getLogger(__name__)


@shared_task(name='bims.tasks.download_chemical_data_to_csv', queue='update')
def download_chemical_data_to_csv(path_file, site_id, download_request_id=None, user_id=None):
    from bims.models.chemical_record import ChemicalRecord
    from bims.models.biological_collection_record import BiologicalCollectionRecord
    from bims.serializers.chemical_records_serializer import (
        ChemicalRecordsOneRowSerializer)
    from bims.utils.celery import memcache_lock

    path_file_hexdigest = sha256(path_file.encode('utf-8')).hexdigest()

    lock_id = '{}-lock-{}'.format(
        download_chemical_data_to_csv.name,
        path_file_hexdigest
    )

    oid = '{0}'.format(path_file_hexdigest)

    with memcache_lock(lock_id, oid) as acquired:
        if acquired:
            queryset = ChemicalRecord.objects.filter(
                Q(location_site_id=site_id) |
                Q(survey__site_id=site_id))

            survey_ids = list(
                queryset.values_list('survey_id', flat=True).distinct()
            )
            bio_source_by_survey = {}
            for bio in BiologicalCollectionRecord.objects.filter(
                survey_id__in=survey_ids
            ).exclude(
                source_reference__isnull=True
            ).select_related('source_reference').distinct('survey_id'):
                label = (
                    bio.source_reference.get_source_unicode()
                    or str(bio.source_reference)
                )
                if label:
                    bio_source_by_survey[bio.survey_id] = label

            serializer = ChemicalRecordsOneRowSerializer(
                queryset,
                many=True,
                context={'bio_source_by_survey': bio_source_by_survey}
            )

            if not serializer.data:
                return

            headers = serializer.data[0].keys()
            rows = serializer.data

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

            if download_request_id and user_id:
                from bims.tasks.email_csv import send_csv_via_email
                send_csv_via_email.delay(
                    user_id=user_id,
                    csv_file=path_file,
                    file_name='Physico-chemical Data',
                    download_request_id=download_request_id
                )

            return

    logger.info(
        'Csv %s is already being processed by another worker',
        path_file)
