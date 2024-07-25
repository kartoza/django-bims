# coding=utf-8
import csv
import logging
from django.contrib.auth import get_user_model
from celery import shared_task


logger = logging.getLogger(__name__)


def process_download_csv_taxa_list(request, csv_file_path, filename, user_id, download_request_id=''):
    from bims.api_views.taxon import TaxaList
    from bims.views.download_csv_taxa_list import TaxaCSVSerializer
    from bims.tasks import send_csv_via_email

    class RequestGet:
        def __init__(self, get_data):
            self.GET = get_data

    # Prepare the request object
    request_get = RequestGet(request)

    # Get the taxa list based on request parameters
    taxa_list = TaxaList.get_taxa_by_parameters(request_get)

    tag_titles = []

    # Define the header update function
    def update_headers(_headers):
        _updated_headers = []
        for header in _headers:
            if header == 'class_name':
                header = 'class'
            elif header == 'taxon_rank':
                header = 'Taxon Rank'
            elif header == 'common_name':
                header = 'Common Name'
            header = header.replace('_or_', '/')
            if not header.istitle() and header not in tag_titles:
                header = header.replace('_', ' ').capitalize()
            if header == 'Sub species':
                header = 'SubSpecies'
            _updated_headers.append(header)
        return _updated_headers

    # Serialize a single item to extract headers
    sample_item = next(taxa_list.iterator())
    sample_serializer = TaxaCSVSerializer(sample_item)
    tag_titles = sample_serializer.context.get('tags', [])
    headers = list(sample_serializer.data.keys())
    updated_headers = update_headers(headers)

    # Write data to CSV
    with open(csv_file_path, 'w', newline='') as csv_file:
        writer = csv.writer(csv_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        writer.writerow(updated_headers)

        # Process each item in the queryset individually
        for taxon in taxa_list.iterator():
            serializer = TaxaCSVSerializer(taxon)
            row = serializer.data
            writer.writerow([value for key, value in row.items()])

    # Send the CSV file via email
    UserModel = get_user_model()
    try:
        user = UserModel.objects.get(id=user_id)
        send_csv_via_email(
            user_id=user.id,
            csv_file=csv_file_path,
            file_name=filename,
            approved=True,
            download_request_id=download_request_id
        )
    except UserModel.DoesNotExist:
        pass


@shared_task(name='bims.tasks.download_csv_taxa_list', queue='update')
def download_csv_taxa_list(request, csv_file, filename, user_id, download_request_id=''):
    from bims.utils.celery import memcache_lock
    lock_id = '{0}-lock-{1}'.format(
        filename,
        csv_file
    )
    oid = '{0}'.format(csv_file)
    with memcache_lock(lock_id, oid) as acquired:
        if acquired:
            return process_download_csv_taxa_list(
                request, csv_file, filename, user_id, download_request_id
            )
    logger.info(
        'Csv %s is already being processed by another worker',
        csv_file)
