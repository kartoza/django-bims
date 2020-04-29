import csv
import logging
from celery import shared_task
from hashlib import md5
from django.core.management import call_command

from bims.models.boundary_type import BoundaryType
from bims.models.boundary import Boundary

logger = logging.getLogger(__name__)


@shared_task(name='bims.tasks.update_search_index', queue='update')
def update_search_index():
    call_command('rebuild_index', verbosity=0, interactive=False)


@shared_task(name='bims.tasks.update_cluster', queue='update')
def update_cluster(ids=None):
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


@shared_task(name='bims.tasks.download_data_to_csv', queue='update')
def download_data_to_csv(path_file, request):
    from bims.serializers.bio_collection_serializer import \
        BioCollectionOneRowSerializer
    from bims.utils.celery import memcache_lock
    from bims.models import BiologicalCollectionRecord
    from bims.api_views.search import Search

    path_file_hexdigest = md5(path_file).hexdigest()

    lock_id = '{0}-lock-{1}'.format(
            download_data_to_csv.name,
            path_file_hexdigest
    )

    oid = '{0}'.format(path_file_hexdigest)

    with memcache_lock(lock_id, oid) as acquired:
        if acquired:
            filters = request
            site_results = None
            search = Search(filters)
            collection_results = search.process_search()

            if not collection_results and site_results:
                site_ids = site_results.values_list('id', flat=True)
                collection_results = BiologicalCollectionRecord.objects.filter(
                    site__id__in=site_ids
                ).distinct()

            serializer = BioCollectionOneRowSerializer(
                collection_results,
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
                if not header.isupper():
                    header = header.replace('_', ' ').capitalize()
                if header.lower() == 'uuid':
                    header = header.upper()
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
