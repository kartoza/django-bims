import csv
import os
from django.conf import settings

from bims.api_views.search import CollectionSearch
from bims.models.taxonomy import Taxonomy
from bims.models.download_request import DownloadRequest
from bims.serializers.checklist_serializer import ChecklistSerializer
from bims.utils.url import parse_url_to_filters


def get_serializer_keys(serializer_class):
    return list(serializer_class().get_fields().keys())


def generate_checklist(download_request_id):
    if not download_request_id:
        return False
    try:
        download_request = DownloadRequest.objects.get(
            id=download_request_id
        )
    except DownloadRequest.DoesNotExist:
        return False

    if download_request and download_request.rejected:
        download_request.processing = False
        download_request.save()
        return False

    if not download_request:
        return False

    filters = parse_url_to_filters(download_request.dashboard_url)
    search = CollectionSearch(filters)

    # returns queryset of collection_records
    collection_records = search.process_search()
    taxa = Taxonomy.objects.filter(
        id__in=list(
            collection_records.values_list(
                'taxonomy_id',
                flat=True)
        )
    )

    taxon_serializer = ChecklistSerializer(
        taxa,
        many=True
    )

    csv_file_path = os.path.join(
        settings.MEDIA_ROOT,
        'checklists', f'checklist_{download_request_id}.csv')
    os.makedirs(os.path.dirname(csv_file_path), exist_ok=True)

    fieldnames = get_serializer_keys(ChecklistSerializer)
    with open(csv_file_path, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()
        for taxon in taxon_serializer.data:
            writer.writerow(taxon)

    # Save file path to download_request
    download_request.processing = False
    download_request.request_file = csv_file_path
    download_request.save()

    return True
