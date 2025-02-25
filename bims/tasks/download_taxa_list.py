# coding=utf-8
import csv
import datetime
import logging
from django.contrib.auth import get_user_model
from celery import shared_task
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import Paragraph, Spacer, SimpleDocTemplate

from bims.scripts.species_keys import (
    ACCEPTED_TAXON, TAXON_RANK,
    COMMON_NAME, CLASS, SUBSPECIES,
    CITES_LISTING
)
from bims.utils.domain import get_current_domain

logger = logging.getLogger(__name__)


def process_download_csv_taxa_list(request, csv_file_path, filename, user_id, download_request_id=''):
    from bims.api_views.taxon import TaxaList
    from bims.views.download_csv_taxa_list import TaxaCSVSerializer
    from bims.tasks import send_csv_via_email
    from bims.models.download_request import DownloadRequest

    class RequestGet:
        def __init__(self, get_data):
            self.GET = get_data

    # Prepare the request object
    request_get = RequestGet(request)

    # Get the taxa list based on request parameters
    taxa_list = TaxaList.get_taxa_by_parameters(request_get)
    total_taxa = taxa_list.count()

    tag_titles = []
    additional_attributes_titles = []

    # Define the header update function
    def update_headers(_headers):
        _updated_headers = []
        for header in _headers:
            if header == 'class_name':
                header = CLASS
            elif header == 'taxon_rank':
                header = TAXON_RANK
            elif header == 'common_name':
                header = COMMON_NAME
            elif header == 'accepted_taxon':
                header = ACCEPTED_TAXON
            header = header.replace('_or_', '/')
            if (
                not header.istitle()
                    and header not in tag_titles
                    and header not in additional_attributes_titles
            ):
                header = header.replace('_', ' ').capitalize()
            if header == 'Subspecies':
                header = SUBSPECIES
            if header.lower().strip() == 'cites_listing':
                header = CITES_LISTING
            _updated_headers.append(header)
        return _updated_headers

    # Serialize a single item to extract headers
    sample_item = next(taxa_list.iterator())
    sample_serializer = TaxaCSVSerializer(sample_item)
    tag_titles = sample_serializer.context.get('tags', [])
    additional_attributes_titles = sample_serializer.context.get(
        'additional_attributes_titles', []
    )
    headers = list(sample_serializer.data.keys())
    updated_headers = update_headers(headers)

    progress = 1

    # Write data to CSV
    with open(csv_file_path, 'w', newline='') as csv_file:
        writer = csv.writer(csv_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        writer.writerow(updated_headers)

        # Process each item in the queryset individually
        for taxon in taxa_list.iterator():
            serializer = TaxaCSVSerializer(taxon)
            row = serializer.data
            writer.writerow([value for key, value in row.items()])

            if progress % 10 == 0 and download_request_id:
                download_request = DownloadRequest.objects.get(
                    id=download_request_id
                )
                download_request.progress = f'{progress}/{total_taxa}'
                download_request.save()

            progress += 1

    # Send the CSV file via email
    UserModel = get_user_model()
    try:
        user = UserModel.objects.get(id=user_id)
        if download_request_id:
            DownloadRequest.objects.filter(
                id=download_request_id
            ).update(
                progress=f'{total_taxa}/{total_taxa}'
            )
        send_csv_via_email(
            user_id=user.id,
            csv_file=csv_file_path,
            file_name=filename,
            approved=True,
            download_request_id=download_request_id
        )
    except UserModel.DoesNotExist:
        pass


def process_download_pdf_taxa_list(
        request, pdf_file_path, filename, user_id, taxon_group_id, download_request_id):
    from bims.tasks import send_csv_via_email
    from bims.models.taxon_group import TaxonGroup
    from bims.api_views.taxon import TaxaList

    class RequestGet:
        def __init__(self, get_data):
            self.GET = get_data

    def get_checklist_paragraphs(taxon_group, taxonomies):
        """
        Build a list of Paragraph objects for the textual "checklist" portion,
        using Times-style fonts.
        """
        # Get the default stylesheet
        styles = getSampleStyleSheet()

        title_style = ParagraphStyle(
            name="TitleStyle",
            parent=styles['Normal'],
            fontName='Times-Bold',
            fontSize=22,
            leading=22,
            alignment=TA_LEFT,
        )

        generated_style = ParagraphStyle(
            name="GeneratedStyle",
            parent=styles['Normal'],
            fontName='Times-Italic',
            fontSize=10,
            leading=12,
            alignment=TA_LEFT,
        )

        genus_style = ParagraphStyle(
            name="GenusStyle",
            parent=styles['Normal'],
            fontName='Times-Bold',
            fontSize=12,
            leading=14,
        )

        species_style = ParagraphStyle(
            name="SpeciesStyle",
            parent=styles['Normal'],
            fontName='Times-Roman',
            fontSize=11,
            leading=14,
        )

        paragraphs = []

        title_text = f"{taxon_group.name} checkList"
        paragraphs.append(Paragraph(title_text, title_style))
        paragraphs.append(Spacer(1, 6))

        current_site = get_current_domain()
        generated_text = (
            f"(generated {datetime.datetime.now().strftime('%a %b %d %H:%M:%S %Y')} "
            f"from {current_site})"
        )
        paragraphs.append(Paragraph(generated_text, generated_style))
        paragraphs.append(Spacer(1, 6))

        paragraphs.append(Spacer(1, 12))

        genus_dict = {}
        species_qs = taxonomies.filter(
            rank__in=['SPECIES', 'SUBSPECIES']
        ).order_by('canonical_name')

        for s in species_qs:
            genus = s.genus
            if not genus:
                continue
            if genus.id not in genus_dict:
                genus_dict[genus.id] = {
                    'obj': genus,
                    'species': []
                }
            genus_dict[genus.id]['species'].append(s)

        for genus_id, info in genus_dict.items():
            g_obj = info['obj']
            genus_line = g_obj.canonical_name
            genus_author = ''
            if g_obj.author and g_obj.author not in genus_line:
                genus_author += f", {g_obj.author}"

            paragraphs.append(Paragraph(f"<i>{genus_line}</i>{genus_author}", genus_style))
            paragraphs.append(Spacer(1, 10))

            for s_obj in info['species']:
                sp_line = f'<i>{s_obj.canonical_name}</i>'
                if s_obj.author:
                    sp_line += f", {s_obj.author}"
                if s_obj.origin:
                    sp_line += f" : {s_obj.origin.upper()}"
                if "type species" in (s_obj.additional_data or {}):
                    sp_line += " (Type species for genus)"

                paragraphs.append(Paragraph(sp_line, species_style))

            paragraphs.append(Spacer(1, 10))

        return paragraphs

    taxon_group = TaxonGroup.objects.get(id=taxon_group_id)

    request_get = RequestGet(request)
    taxonomies = TaxaList.get_taxa_by_parameters(request_get)

    doc = SimpleDocTemplate(
        pdf_file_path,
        pagesize=A4,
        rightMargin=50,
        leftMargin=50,
        topMargin=50,
        bottomMargin=50
    )

    story = []

    checklist_paragraphs = get_checklist_paragraphs(taxon_group, taxonomies)
    story.extend(checklist_paragraphs)
    doc.build(story)

    UserModel = get_user_model()
    try:
        user = UserModel.objects.get(id=user_id)
        send_csv_via_email(
            user_id=user.id,
            csv_file=pdf_file_path,
            file_name=filename,
            approved=True,
            download_request_id=download_request_id
        )
    except UserModel.DoesNotExist:
        pass


@shared_task(name='bims.tasks.download_csv_taxa_list', queue='update')
def download_taxa_list(
        request, csv_file, filename, user_id, output = 'csv', download_request_id='', taxon_group_id = None):
    from bims.utils.celery import memcache_lock
    lock_id = '{0}-lock-{1}'.format(
        filename,
        csv_file
    )
    oid = '{0}'.format(csv_file)
    with memcache_lock(lock_id, oid) as acquired:
        if acquired:
            if output == 'csv':
                return process_download_csv_taxa_list(
                    request, csv_file, filename, user_id, download_request_id
                )
            else:
                return process_download_pdf_taxa_list(
                    request, csv_file, filename, user_id, taxon_group_id, download_request_id
                )
    logger.info(
        'Csv %s is already being processed by another worker',
        csv_file)
