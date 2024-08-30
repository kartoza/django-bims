import csv
import os
from django.conf import settings
from django.http import Http404
from preferences import preferences
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, TableStyle, Table, Spacer
from reportlab.platypus.para import Paragraph
from rest_framework.response import Response
from rest_framework.views import APIView

from bims.api_views.search import CollectionSearch
from bims.enums import TaxonomicRank
from bims.models.taxonomy import Taxonomy
from bims.utils.domain import get_current_domain
from bims.models.download_request import DownloadRequest
from bims.serializers.checklist_serializer import (
    ChecklistSerializer,
    ChecklistPDFSerializer
)
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
    collection_records = search.process_search()
    module_name = ''

    if collection_records.count() > 0:
        module_name = collection_records.values_list(
            'module_group__name',
            flat=True
        )[0]

    if (
        download_request.resource_type and
        download_request.resource_type.lower() == 'pdf'
    ):
        return generate_pdf_checklist(
            download_request, module_name, collection_records, batch_size)
    else:
        return generate_csv_checklist(
            download_request, module_name, collection_records, batch_size)


def generate_csv_checklist(download_request, module_name, collection_records, batch_size):
    site_domain_name = get_current_domain()

    csv_file_path = os.path.join(
        settings.MEDIA_ROOT,
        'checklists',
        f'{site_domain_name}_checklist_{module_name}_{download_request.id}.csv')
    os.makedirs(os.path.dirname(csv_file_path), exist_ok=True)

    fieldnames = [key for key in get_serializer_keys(ChecklistSerializer) if key != 'id']
    custom_header = get_custom_header(fieldnames, CSV_HEADER_TITLE)

    taxonomy_collection_records = collection_records.distinct('taxonomy')
    taxonomy_collection_records_count = taxonomy_collection_records.count()

    written_taxa_ids = set()

    with open(csv_file_path, 'a', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        if not written_taxa_ids:
            # Manually write header using writerow
            writer.writerow(dict(zip(fieldnames, custom_header)))

        for start in range(0, taxonomy_collection_records_count, batch_size):
            batch = taxonomy_collection_records[start:start + batch_size]
            process_batch(batch, writer, written_taxa_ids, collection_records)
            download_request.progress = (
                f'{start}/{taxonomy_collection_records_count}'
            )
            download_request.save()

    download_request.progress = (
        f'{taxonomy_collection_records_count}/{taxonomy_collection_records_count}'
    )
    download_request.processing = False
    download_request.request_file = csv_file_path
    download_request.request_category = f'{module_name} Checklist'
    download_request.save()

    return True


def generate_pdf_checklist(download_request, module_name, collection_records, batch_size):
    site_domain_name = get_current_domain()
    pdf_file_path = os.path.join(
        settings.MEDIA_ROOT,
        'checklists',
        f'{site_domain_name}_checklist_{module_name}_{download_request.id}.pdf')
    os.makedirs(os.path.dirname(pdf_file_path), exist_ok=True)

    written_taxa_ids = set()
    all_taxa = []

    taxonomy_collection_records = collection_records.distinct('taxonomy')
    taxonomy_collection_records_count = taxonomy_collection_records.count()

    for start in range(0, taxonomy_collection_records_count, batch_size):
        batch = taxonomy_collection_records[start:start + batch_size]
        record_taxonomy_ids = batch.values_list('taxonomy_id', flat=True)
        unique_taxonomy_ids = set(record_taxonomy_ids) - written_taxa_ids

        if unique_taxonomy_ids:
            taxa = Taxonomy.objects.filter(
                id__in=unique_taxonomy_ids
            ).filter(
                rank__in=[
                    TaxonomicRank.SPECIES.name,
                    TaxonomicRank.SUBSPECIES.name]
            ).order_by(
                'scientific_name'
            )
            taxon_serializer = ChecklistPDFSerializer(taxa, many=True)
            for taxon in taxon_serializer.data:
                written_taxa_ids.add(taxon['id'])
                del taxon['id']
                all_taxa.append([
                    Paragraph(taxon['scientific_name'], getSampleStyleSheet()['Normal']),
                    Paragraph(taxon['common_name'], getSampleStyleSheet()['Normal']),
                    Paragraph(taxon['threat_status'], getSampleStyleSheet()['Normal']),
                    Paragraph(taxon['sources'], getSampleStyleSheet()['Normal'])
                ])
        download_request.progress = (
            f'{start}/{taxonomy_collection_records_count}'
        )
        download_request.save()

    # Generate the PDF
    doc = SimpleDocTemplate(
        pdf_file_path,
        pagesize=landscape(A4), topMargin=0.5 * cm, bottomMargin=0.35 * cm)
    elements = []

    # Define table style
    style_table = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), '#0D3511'),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 5),
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
        ('RIGHTPADDING', (0, 0), (-1, -1), 5),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ])

    data = [
               ['Accepted Scientific name and authority',
                'Common Name',
                'Threat Status',
                'Sources']] + all_taxa
    table_width = doc.width
    col_widths = [table_width * 0.35, table_width * 0.30, table_width * 0.15, table_width * 0.30]

    table = Table(data, colWidths=col_widths)
    table.setStyle(style_table)

    elements.append(table)
    doc.build(elements)

    download_request.progress = (
        f'{taxonomy_collection_records_count}/{taxonomy_collection_records_count}'
    )
    download_request.processing = False
    download_request.request_file = pdf_file_path
    download_request.request_category = f'{module_name} Checklist'
    download_request.save()

    return True


def process_batch(batch, writer, written_taxa_ids, collection_records):
    """
    Process a batch of collection records and write unique taxa to the CSV file.
    Args:
        batch (QuerySet): A batch of collection records.
        writer (csv.DictWriter): CSV writer object.
        written_taxa_ids (set): Set of already written taxa IDs to avoid duplication.
        collection_records (QuerySet): Filtered collection records
    """
    record_taxonomy_ids = batch.values_list('taxonomy_id', flat=True)
    unique_taxonomy_ids = set(record_taxonomy_ids) - written_taxa_ids

    if unique_taxonomy_ids:
        taxa = Taxonomy.objects.filter(id__in=unique_taxonomy_ids)
        taxon_serializer = ChecklistSerializer(
            taxa,
            many=True,
            context={
                'collection_records': collection_records
            }
        )

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
