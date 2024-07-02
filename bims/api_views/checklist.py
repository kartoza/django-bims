import csv
import os
from django.conf import settings
from django.http import Http404
from preferences import preferences
from rest_framework.response import Response
from rest_framework.views import APIView

from bims.api_views.search import CollectionSearch
from bims.models.taxonomy import Taxonomy
from bims.models.download_request import DownloadRequest
from bims.serializers.checklist_serializer import ChecklistSerializer
from bims.utils.url import parse_url_to_filters
from bims.tasks.checklist import download_checklist
from bims.tasks.email_csv import send_csv_via_email


CSV_HEADER_TITLE = {
    'class_name': 'Class',
    'scientific_name': 'Accepted Scientific name and authority',
    'cites_listing': 'CITES listing',
    'park_or_mpa_name': 'Park or MPA name'
}


def get_custom_header(fieldnames, header_title_dict):
    custom_header = []
    for field in fieldnames:
        if field in header_title_dict:
            custom_header.append(header_title_dict[field])
        else:
            custom_header.append(field.replace('_', ' ').capitalize())
    return custom_header


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
    batch_size = 1000
    collection_records = search.process_search().distinct('taxonomy')

    csv_file_path = os.path.join(
        settings.MEDIA_ROOT,
        'checklists',
        f'checklist_{download_request_id}.csv')
    os.makedirs(os.path.dirname(csv_file_path), exist_ok=True)

    fieldnames = [key for key in get_serializer_keys(ChecklistSerializer) if key != 'id']
    custom_header = get_custom_header(fieldnames, CSV_HEADER_TITLE)

    written_taxa_ids = set()

    with open(csv_file_path, 'a', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        if not written_taxa_ids:
            # Manually write header using writerow
            writer.writerow(dict(zip(fieldnames, custom_header)))

        for start in range(0, collection_records.count(), batch_size):
            batch = collection_records[start:start + batch_size]
            process_batch(batch, writer, written_taxa_ids)

    # Save file path to download_request
    download_request.processing = False
    download_request.request_file = csv_file_path
    download_request.save()

    return True


def process_batch(batch, writer, written_taxa_ids):
    """
    Process a batch of collection records and write unique taxa to the CSV file.
    Args:
        batch (QuerySet): A batch of collection records.
        writer (csv.DictWriter): CSV writer object.
        written_taxa_ids (set): Set of already written taxa IDs to avoid duplication.
    """
    record_taxonomy_ids = batch.values_list('taxonomy_id', flat=True)
    unique_taxonomy_ids = set(record_taxonomy_ids) - written_taxa_ids

    if unique_taxonomy_ids:
        taxa = Taxonomy.objects.filter(id__in=unique_taxonomy_ids)
        taxon_serializer = ChecklistSerializer(taxa, many=True)

        for taxon in taxon_serializer.data:
            written_taxa_ids.add(taxon['id'])
            del taxon['id']
            writer.writerow(taxon)


class DownloadChecklistAPIView(APIView):

    def post(self, request, *args, **kwargs):
        auto_approved = not preferences.SiteSetting.enable_download_request_approval
        download_request_id = self.request.POST.get(
            'downloadRequestId', None)

        if not download_request_id:
            raise Http404('Missing download request id')

        download_request = DownloadRequest.objects.get(
            id=download_request_id
        )

        if download_request.request_file and download_request.approved:
            send_csv_via_email.delay(
                user_id=self.request.user.id,
                csv_file=download_request.request_file.path,
                file_name='Checklist',
                download_request_id=download_request_id
            )
        else:
            if auto_approved and not download_request.approved:
                download_request.approved = True
                download_request.save()

            download_checklist.delay(
                download_request_id,
                auto_approved,
                download_request.requester.id)

        return Response({
            'status': 'processing',
        })
