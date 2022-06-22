import logging
import csv
import time
import gc

from bims.models.download_request import DownloadRequest

logger = logging.getLogger(__name__)


def queryset_iterator(qs, batch_size = 500, gc_collect = True):
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


def write_to_csv(headers: list,
                 rows: list,
                 path_file: str,
                 current_csv_row: int = 0):
    formatted_headers = []
    if headers:
        for header in headers:
            if header == 'class_name':
                header = 'class'
            header = header.replace('_or_', '/')
            if not header.isupper():
                header = header.replace('_', ' ').capitalize()
            if header.lower() == 'uuid':
                header = header.upper()
            formatted_headers.append(header)

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
        user_id=None
):
    from django.contrib.auth import get_user_model
    from bims.serializers.bio_collection_serializer import (
        BioCollectionOneRowSerializer
    )
    from bims.api_views.search import CollectionSearch
    from bims.models import BiologicalCollectionRecord
    from bims.api_views.csv_download import send_csv_via_email

    start = time.time()

    filters = request
    download_request_id = filters.get('downloadRequestId', '')
    download_request = None
    if download_request_id:
        try:
            download_request = DownloadRequest.objects.get(
                id=download_request_id
            )
        except DownloadRequest.DoesNotExist:
            pass

    site_results = None
    search = CollectionSearch(filters)
    collection_results = search.process_search()
    total_records = collection_results.count()

    logger.debug('Total records : {}'.format(total_records))

    logger.debug('Search time : {}'.format(
        round(time.time() - start, 2))
    )

    if not collection_results and site_results:
        site_ids = site_results.values_list('id', flat=True)
        collection_results = BiologicalCollectionRecord.objects.filter(
            site__id__in=site_ids
        ).distinct()

    current_csv_row = 0
    record_number = 100 if total_records >= 100 else total_records
    headers = []
    collection_data = []

    for obj in queryset_iterator(collection_results):
        collection_data.append(obj)
        if len(collection_data) >= record_number:
            serializer = BioCollectionOneRowSerializer(
                collection_data,
                many=True,
                context={
                    'header': headers
                }
            )
            rows = serializer.data
            headers = serializer.context['header']
            start_index = current_csv_row
            current_csv_row = write_to_csv(
                headers,
                rows,
                path_file,
                current_csv_row
            )
            logger.debug('Serialize time {0}:{1}: {2}'.format(
                start_index,
                current_csv_row,
                round(time.time() - start, 2))
            )
            if download_request:
                download_request.progress = f'{start_index}/{total_records}'
                download_request.save()
            del rows
            del collection_data
            del serializer
            collection_data = []
            gc.collect()

    if collection_data:
        serializer = BioCollectionOneRowSerializer(
            collection_data,
            many=True,
            context={
                'header': headers
            }
        )
        rows = serializer.data
        headers = serializer.context['header']
        start_index = current_csv_row
        current_csv_row = write_to_csv(
            headers,
            rows,
            path_file,
            current_csv_row
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
                user=user,
                csv_file=path_file,
                download_request_id=download_request_id
            )
        except UserModel.DoesNotExist:
            pass
    return
