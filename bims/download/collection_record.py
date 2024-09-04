import logging
import csv
import os
import time
import gc

from bims.models.download_request import DownloadRequest
from bims.scripts.collection_csv_keys import PARK_OR_MPA_NAME

logger = logging.getLogger(__name__)


def queryset_iterator(qs, batch_size=500, gc_collect=True):
    iterator = (
        qs.values_list('pk', flat=True).order_by('pk').distinct().iterator()
    )
    eof = False
    while not eof:
        primary_key_buffer = []
        try:
            while len(primary_key_buffer) < batch_size:
                primary_key_buffer.append(next(iterator))
        except StopIteration:
            eof = True
        for obj in qs.filter(
                pk__in=primary_key_buffer
        ).order_by('pk').iterator():
            yield obj
        if gc_collect:
            gc.collect()


HEADER_TITLES = {
    'class_name': 'Class',
    'sub_species': 'SubSpecies',
    'cites_listing': 'CITES listing',
    'park_or_mpa_name': PARK_OR_MPA_NAME,
    'authors': 'Author(s)'
}


def format_header(header: str) -> str:
    if header in HEADER_TITLES:
        return HEADER_TITLES[header]
    if header.lower() == 'uuid':
        return header.upper()
    header = header.replace('_or_', '/')
    if not header[0].isupper():
        header = header.replace('_', ' ').capitalize()
    return header


def write_to_csv(headers: list,
                 rows: list,
                 path_file: str,
                 current_csv_row: int = 0):
    formatted_headers = [format_header(header) for header in headers]
    with open(path_file, 'a') as csv_file:
        if headers:
            writer = csv.DictWriter(csv_file, fieldnames=formatted_headers)
            if current_csv_row == 0:
                writer.writeheader()
            writer.fieldnames = headers
        for row in rows:
            try:
                current_csv_row += 1
                writer.writerow(row)
            except:  # noqa
                continue

    return current_csv_row


def download_collection_records(
        path_file,
        request,
        send_email=False,
        user_id=None,
        process_id=None
):
    from django.contrib.auth import get_user_model
    from bims.serializers.bio_collection_serializer import (
        BioCollectionOneRowSerializer
    )
    from bims.api_views.search import CollectionSearch
    from bims.models import BiologicalCollectionRecord
    from bims.tasks.email_csv import send_csv_via_email
    from preferences import preferences

    project_name = preferences.SiteSetting.project_name

    exclude_fields = []
    headers = []

    if project_name.lower() == 'sanparks':
        exclude_fields = [
            'user_river_name',
            'river_name',
            'user_wetland_name',
            'wetland_name',
            'user_geomorphological_zone',
            'hydroperiod',
            'wetland_indicator_status',
            'broad_biotope',
            'specific_biotope',
            'substratum',
            'analyst',
            'analyst_institute',
            'sampling_effort_measure',
            'sampling_effort_value',
            'abundance_value',
            'abundance_measure'
        ]

    def get_download_request(request_id):
        try:
            return DownloadRequest.objects.get(
                id=request_id
            )
        except DownloadRequest.DoesNotExist:
            return None

    def write_batch_to_csv(header, rows, path_file, start_index, upload_template_headers=[]):
        bio_serializer = (
            BioCollectionOneRowSerializer(
                rows, many=True,
                context={
                    'header': header,
                    'exclude_fields': exclude_fields,
                    'upload_template_headers': upload_template_headers
                })
        )
        bio_data = bio_serializer.data
        if len(header) == 0:
            header = bio_serializer.context['header']
            if upload_template_headers:
                park_key = PARK_OR_MPA_NAME
                if park_key in header:
                    header.insert(1, header.pop(header.index(park_key)))
        csv_row = write_to_csv(
            header,
            bio_data,
            path_file,
            start_index)
        del bio_serializer
        return csv_row, header

    start = time.time()

    filters = request
    download_request_id = filters.get('downloadRequestId', '')
    download_request = get_download_request(download_request_id)

    site_results = None
    search = CollectionSearch(filters, user_id if user_id else None)
    collection_results = search.process_search()
    total_records = collection_results.count()

    if not collection_results and site_results:
        site_ids = site_results.values_list('id', flat=True)
        collection_results = BiologicalCollectionRecord.objects.filter(
            site__id__in=site_ids
        ).distinct()

    current_csv_row = 0
    record_number = min(total_records, 100)
    collection_data = []

    if download_request and download_request.rejected:
        return

    taxon_group = collection_results.first().module_group
    upload_template_headers = []
    if taxon_group.occurrence_upload_template:
        try:
            with open(taxon_group.occurrence_upload_template.path, 'r', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                upload_template_headers = reader.fieldnames
        except FileNotFoundError:
            upload_template_headers = []

    for obj in queryset_iterator(collection_results):
        collection_data.append(obj)
        if len(collection_data) >= record_number:
            start_index = current_csv_row
            current_csv_row, headers = write_batch_to_csv(
                headers,
                collection_data,
                path_file,
                current_csv_row,
                upload_template_headers
            )

            logger.debug('Serialize time {0}:{1}: {2}'.format(
                start_index,
                current_csv_row,
                round(time.time() - start, 2))
            )

            del collection_data
            collection_data = []

            gc.collect()

            download_request = get_download_request(download_request_id)

            if download_request.rejected:
                logger.debug('Download request is rejected, closing.')
                try:
                    os.remove(path_file)
                except Exception: # noqa
                    pass
                return
            else:
                download_request.progress = f'{start_index}/{total_records}'
                download_request.save()

    if collection_data:
        start_index = current_csv_row
        current_csv_row, headers = write_batch_to_csv(
            headers,
            collection_data,
            path_file,
            current_csv_row,
            upload_template_headers
        )
        logger.debug('Serialize time {0}:{1}: {2}'.format(
            start_index,
            current_csv_row,
            round(time.time() - start, 2))
        )

    logger.debug('Serialize time : {}'.format(
        round(time.time() - start, 2))
    )

    if download_request:
        download_request = get_download_request(download_request_id)
        download_request.progress = f'{current_csv_row}/{total_records}'
        download_request.save()

    logger.debug(
        'Write csv time : {}'.format(
            round(time.time() - start, 2)
        )
    )

    if send_email and user_id:
        UserModel = get_user_model()
        try:
            user = UserModel.objects.get(id=user_id)
            send_csv_via_email(
                user_id=user.id,
                file_name='Occurrence Data',
                csv_file=path_file,
                download_request_id=download_request_id
            )
        except UserModel.DoesNotExist:
            pass
    return
