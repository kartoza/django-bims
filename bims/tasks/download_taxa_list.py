# coding=utf-8
import csv
import logging
from django.contrib.auth import get_user_model
from celery import shared_task
from bims.api_views.taxon import TaxaList

logger = logging.getLogger(__name__)


def process_download_csv_taxa_list(request, csv_file_path, filename, user_id):
    from bims.views.download_csv_taxa_list import TaxaCSVSerializer
    from bims.api_views.csv_download import send_csv_via_email
    class RequestGet:
        def __init__(self, get_data):
            self.GET = get_data
    request_get = RequestGet(request)
    taxa_list = TaxaList.get_taxa_by_parameters(request_get)

    taxa_serializer = TaxaCSVSerializer(
        taxa_list,
        many=True
    )

    rows = taxa_serializer.data
    headers = taxa_serializer.context['headers']

    with open(csv_file_path, 'w') as csv_file:
        writer = csv.writer(
            csv_file, delimiter=',', quotechar='"',
            quoting=csv.QUOTE_MINIMAL)

        updated_headers = []

        for header in headers:
            if header == 'class_name':
                header = 'class'
            elif header == 'taxon_rank':
                header = 'Taxon Rank'
            elif header == 'common_name':
                header = 'Common Name'
            header = header.replace('_or_', '/')
            if not header.istitle():
                header = header.replace('_', ' ').capitalize()
            updated_headers.append(header)
        writer.writerow(updated_headers)

        for taxon_row in rows:
            writer.writerow([value for key, value in taxon_row.items()])

    UserModel = get_user_model()
    try:
        user = UserModel.objects.get(id=user_id)
        send_csv_via_email(
            user=user,
            csv_file=csv_file_path,
            file_name=filename
        )
    except UserModel.DoesNotExist:
        pass


@shared_task(name='bims.tasks.download_csv_taxa_list', queue='update')
def download_csv_taxa_list(request, csv_file, filename, user_id):
    from bims.utils.celery import memcache_lock
    lock_id = '{0}-lock-{1}'.format(
        filename,
        csv_file
    )
    oid = '{0}'.format(csv_file)
    with memcache_lock(lock_id, oid) as acquired:
        if acquired:
            return process_download_csv_taxa_list(
                request, csv_file, filename, user_id
            )
    logger.info(
        'Csv %s is already being processed by another worker',
        csv_file)
