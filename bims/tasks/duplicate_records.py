import csv
import logging
from bims.models import BiologicalCollectionRecord
from bims.serializers.bio_collection_serializer import BioCollectionOneRowSerializer
from celery import shared_task
from django.db.models import Q

logger = logging.getLogger('bims')


@shared_task(name='bims.tasks.download_duplicated_records_to_csv', queue='update')
def download_duplicated_records_to_csv(queryset, path_file):
    from bims.utils.celery import memcache_lock

    lock_id = '{0}-lock-{1}'.format(
        download_duplicated_records_to_csv.name,
        path_file
    )

    oid = '{0}'.format(path_file)
    query = Q()

    with memcache_lock(lock_id, oid) as acquired:
        if acquired:
            for value in queryset:
                query = query | Q(Q(site_id=value['site_id']) &
                                  Q(taxonomy_id=value['taxonomy_id']) &
                                  Q(collection_date=value['collection_date']))
            data = BiologicalCollectionRecord.objects.filter(query)
            serializer = BioCollectionOneRowSerializer(
                data,
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
