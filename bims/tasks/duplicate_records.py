import csv
import logging
from bims.models import BiologicalCollectionRecord
from bims.serializers.bio_collection_serializer import BioCollectionOneRowSerializer
from celery import shared_task
from django.db.models import Q

logger = logging.getLogger('bims')


@shared_task(name='bims.tasks.download_duplicated_records_to_csv', queue='update')
def download_duplicated_records_to_csv(path_file):
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
                survey_date = value['survey__date']
                if isinstance(survey_date, str):
                    if 'T' in survey_date:
                        survey_date = survey_date.split('T')[0]
                else:
                    survey_date = str(survey_date)
                query = Q(Q(site_id=value['site_id']) &
                          Q(biotope_id=value['biotope_id']) &
                          Q(specific_biotope_id=value['specific_biotope_id']) &
                          Q(substratum_id=value['substratum_id']) &
                          Q(taxonomy_id=value['taxonomy_id']) &
                          Q(survey__date=survey_date) &
                          Q(abundance_number=value['abundance_number']))
                records = BiologicalCollectionRecord.objects.filter(
                    query
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

            return

    logger.info(
        'Csv %s is already being processed by another worker',
        path_file)
