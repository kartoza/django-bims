import csv
import os
from datetime import datetime
from django.conf import settings
from django.db.models import F
from django.http import Http404
from preferences import preferences
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.platypus import SimpleDocTemplate, TableStyle, Table, Spacer, Image
from reportlab.platypus.para import Paragraph
from rest_framework.response import Response
from rest_framework.views import APIView

from django.contrib.auth import get_user_model


def get_theme_colors():
    """Get theme colors from CustomTheme or return defaults."""
    try:
        from bims_theme.models.theme import CustomTheme
        theme = CustomTheme.objects.filter(is_enabled=True).first()
        if theme:
            return {
                'primary': theme.main_accent_color or '#18A090',
                'secondary': theme.secondary_accent_color or '#DBAF00',
                'text': theme.main_button_text_color or '#FFFFFF',
                'site_name': theme.site_name or 'BIMS',
                'logo_path': theme.logo.path if theme.logo else None,
            }
    except Exception:
        pass
    return {
        'primary': '#18A090',
        'secondary': '#DBAF00',
        'text': '#FFFFFF',
        'site_name': 'BIMS',
        'logo_path': None,
    }

from bims.api_views.search import CollectionSearch
from bims.enums import TaxonomicRank
from bims.models import LocationContext
from bims.models.taxonomy import Taxonomy
from bims.scripts.collection_csv_keys import PARK_OR_MPA_NAME
from bims.utils.domain import get_current_domain
from bims.models.download_request import DownloadRequest
from bims.serializers.checklist_serializer import (
    ChecklistSerializer,
    ChecklistPDFSerializer
)
from bims.utils.site_code import SANPARK_PARK_KEY
from bims.utils.url import parse_url_to_filters
from bims.tasks.checklist import download_checklist
from bims.tasks.email_csv import send_csv_via_email


CSV_HEADER_TITLE = {
    'class_name': 'Class',
    'scientific_name': 'Accepted Scientific name and authority',
    'cites_listing': 'CITES listing',
    'tops': 'TOPS',
    'park_or_mpa_name': 'Park or MPA name',
    'include or exclude': 'Include/Exclude',
    'gbif_coordinate_uncertainty_m': 'GBIF coordinate uncertainty (m)',
    'gbif_coordinate_precision': 'GBIF coordinate precision'
}

User = get_user_model()


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


def checklist_collection_records(download_request: DownloadRequest):
    filters = parse_url_to_filters(
        download_request.dashboard_url
    )
    search = CollectionSearch(
        filters,
        bypass_data_type_checks=True)
    collection_records = search.process_search()
    return collection_records


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

    batch_size = 1000
    collection_records = checklist_collection_records(
        download_request
    )
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


def _format_park_column_title(park_name):
    name = (park_name or '').strip()
    if not name:
        return ''
    if 'National Park' in name:
        name = name.replace('National Park', 'NP').strip()
    elif not name.endswith('NP'):
        name = f'{name} NP'
    return f'{name} invasion status'


def _slugify_park_fieldname(park_name):
    import re
    base = (park_name or '').strip().lower()
    base = base.replace('national park', 'np')
    base = re.sub(r'\W+', '_', base)
    base = base.strip('_')
    if not base:
        return ''
    return f'invasion_status_{base}'


def _get_distinct_parks_for_collection(collection_records):
    site_ids = (
        collection_records
        .exclude(site__isnull=True)
        .values_list('site_id', flat=True)
        .distinct()
    )
    if not site_ids:
        return []

    park_names = (
        LocationContext.objects
        .filter(
            site_id__in=site_ids,
            group__name__icontains=SANPARK_PARK_KEY
        )
        .values_list('value', flat=True)
        .distinct()
    )

    return [name.strip() for name in park_names if name and name.strip()]


def generate_csv_checklist(download_request, module_name, collection_records, batch_size):
    site_domain_name = get_current_domain()

    csv_file_path = os.path.join(
        settings.MEDIA_ROOT,
        'checklists',
        f'{site_domain_name}_checklist_{module_name}_{download_request.id}.csv')
    os.makedirs(os.path.dirname(csv_file_path), exist_ok=True)

    fieldnames = [key for key in get_serializer_keys(ChecklistSerializer) if key != 'id']

    header_title_dict = dict(CSV_HEADER_TITLE)
    park_field_map = {}

    if preferences.SiteSetting.project_name == 'sanparks':
        park_names = _get_distinct_parks_for_collection(collection_records)
        for park_name in park_names:
            field_key = _slugify_park_fieldname(park_name)
            if not field_key:
                continue
            park_field_map[park_name] = field_key
            fieldnames.append(field_key)
            header_title_dict[field_key] = _format_park_column_title(park_name)

    custom_header = get_custom_header(fieldnames, header_title_dict)

    taxonomy_collection_records = (
        collection_records.distinct(
            'taxonomy__scientific_name'
        ).order_by('taxonomy__scientific_name')
    )
    taxonomy_collection_records_count = taxonomy_collection_records.count()
    taxonomy_ids = list(taxonomy_collection_records.values_list('taxonomy_id', flat=True))

    written_taxa_ids = set()

    with open(csv_file_path, 'a', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        if not written_taxa_ids:
            writer.writerow(dict(zip(fieldnames, custom_header)))

        for start in range(0, taxonomy_collection_records_count, batch_size):
            batch = taxonomy_ids[start:start + batch_size]
            process_batch(
                batch,
                writer,
                written_taxa_ids,
                collection_records,
                park_field_map,
            )
            download_request.progress = (
                f'{start}/{taxonomy_collection_records_count}'
            )
            download_request.save()

    download_request.progress = (
        f'{taxonomy_collection_records_count}/{taxonomy_collection_records_count}'
    )
    download_request.processing = False
    # Store path relative to MEDIA_ROOT for proper URL generation
    csv_relative_path = os.path.relpath(csv_file_path, settings.MEDIA_ROOT)
    download_request.request_file = csv_relative_path
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

    if os.path.exists(pdf_file_path):
        os.remove(pdf_file_path)

    # Get theme colors
    theme = get_theme_colors()
    primary_color = colors.HexColor(theme['primary'])
    text_color = colors.HexColor(theme['text'])

    written_taxa_ids = set()
    all_taxa = []
    common_names_and_count = {}

    taxonomy_collection_records = (
        collection_records.distinct(
            'taxonomy__scientific_name'
        ).order_by('taxonomy__scientific_name')
    )
    taxonomy_collection_records_count = taxonomy_collection_records.count()
    taxonomy_ids = list(taxonomy_collection_records.values_list('taxonomy_id', flat=True))

    # Create custom styles
    styles = getSampleStyleSheet()
    normal_style = ParagraphStyle(
        'CustomNormal',
        parent=styles['Normal'],
        fontSize=9,
        leading=11,
    )
    italic_style = ParagraphStyle(
        'CustomItalic',
        parent=styles['Normal'],
        fontSize=9,
        leading=11,
        fontName='Helvetica-Oblique',
    )

    for start in range(0, taxonomy_collection_records_count, batch_size):
        record_taxonomy_ids = taxonomy_ids[start:start + batch_size]
        unique_taxonomy_ids = set(record_taxonomy_ids) - written_taxa_ids

        if unique_taxonomy_ids:
            taxa = Taxonomy.objects.filter(
                id__in=unique_taxonomy_ids
            ).order_by(
                'scientific_name'
            ).filter(
                rank__in=[
                    TaxonomicRank.SPECIES.name,
                    TaxonomicRank.SUBSPECIES.name]
            )
            taxon_serializer = ChecklistPDFSerializer(
                taxa,
                many=True,
                context={
                    'collection_records': collection_records
                }
            )
            for taxon in taxon_serializer.data:
                written_taxa_ids.add(taxon['id'])
                common_name = taxon['common_name'].lower().strip()

                taxon_entry = [
                    Paragraph(taxon['scientific_name'], italic_style),
                    Paragraph(taxon['common_name'], normal_style),
                    Paragraph(taxon['threat_status'], normal_style),
                    Paragraph(taxon['sources'], normal_style)
                ]

                if common_name != '':
                    if common_name not in common_names_and_count:
                        common_names_and_count[common_name] = (taxon['occurrence_records'], len(all_taxa))
                        all_taxa.append(taxon_entry)
                    else:
                        existing_occurrence_records, index = common_names_and_count[common_name]
                        if taxon['occurrence_records'] > existing_occurrence_records:
                            common_names_and_count[common_name] = (taxon['occurrence_records'], index)
                            all_taxa[index] = taxon_entry
                        else:
                            all_taxa.append(taxon_entry)
                else:
                    all_taxa.append(taxon_entry)

                del taxon['id']
                del taxon['occurrence_records']

        download_request.progress = (
            f'{start}/{taxonomy_collection_records_count}'
        )
        download_request.save()

    # Generate the PDF with themed styling
    doc = SimpleDocTemplate(
        pdf_file_path,
        pagesize=landscape(A4),
        topMargin=1.5 * cm,
        bottomMargin=1 * cm,
        leftMargin=1 * cm,
        rightMargin=1 * cm
    )
    elements = []

    # Add header with site branding
    header_style = ParagraphStyle(
        'Header',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=primary_color,
        spaceAfter=6,
        alignment=TA_LEFT,
    )
    subtitle_style = ParagraphStyle(
        'Subtitle',
        parent=styles['Normal'],
        fontSize=11,
        textColor=colors.gray,
        spaceAfter=12,
    )

    # Site name and report title
    title = f"{theme['site_name']} - Species Checklist"
    if module_name:
        title = f"{theme['site_name']} - {module_name} Checklist"
    elements.append(Paragraph(title, header_style))

    # Subtitle with date and count
    generated_date = datetime.now().strftime('%d %B %Y')
    species_count = len(all_taxa)
    subtitle = f"Generated on {generated_date} | {species_count} species"
    elements.append(Paragraph(subtitle, subtitle_style))
    elements.append(Spacer(1, 0.3 * cm))

    # Define table style with theme colors
    style_table = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), primary_color),
        ('TEXTCOLOR', (0, 0), (-1, 0), text_color),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('TOPPADDING', (0, 0), (-1, 0), 8),
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.Color(0.8, 0.8, 0.8)),
        ('BOX', (0, 0), (-1, -1), 1, primary_color),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 1), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 4),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.Color(0.97, 0.97, 0.97)]),
    ])

    # Build data table
    header_row = [
        'Scientific Name',
        'Common Name',
        'Conservation Status',
        'Data Sources'
    ]
    data = [header_row] + all_taxa

    table_width = doc.width
    col_widths = [table_width * 0.32, table_width * 0.28, table_width * 0.15, table_width * 0.25]

    table = Table(data, colWidths=col_widths, repeatRows=1)
    table.setStyle(style_table)

    elements.append(table)

    # Add footer
    elements.append(Spacer(1, 0.5 * cm))
    footer_style = ParagraphStyle(
        'Footer',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.gray,
        alignment=TA_CENTER,
    )
    footer_text = f"Generated by {theme['site_name']} | {site_domain_name}"
    elements.append(Paragraph(footer_text, footer_style))

    doc.build(elements)

    download_request.progress = (
        f'{taxonomy_collection_records_count}/{taxonomy_collection_records_count}'
    )
    download_request.processing = False
    # Store path relative to MEDIA_ROOT for proper URL generation
    pdf_relative_path = os.path.relpath(pdf_file_path, settings.MEDIA_ROOT)
    download_request.request_file = pdf_relative_path
    download_request.request_category = f'{module_name} Checklist'
    download_request.save()

    return True


def _get_invasion_status_for_taxon_parks(taxon_obj, park_field_map, collection_records):
    if not park_field_map:
        return {}

    results = {field_key: '' for field_key in park_field_map.values()}

    for park_name, field_key in park_field_map.items():
        is_key = f'IS_{park_name}'
        statuses = set()
        addl = getattr(taxon_obj, 'additional_data', None) or {}
        val = addl.get(is_key)
        if isinstance(val, str):
            val = val.strip()
        if val:
            statuses.add(val)
        if statuses:
            results[field_key] = ', '.join(sorted(statuses))

    return results


def process_batch(record_taxonomy_ids, writer, written_taxa_ids, collection_records, park_field_map=None):
    """
    Process a batch of collection records and write unique taxa to the CSV file.
    Args:
        record_taxonomy_ids (list): list of taxonomy ids
        writer (csv.DictWriter): CSV writer object.
        written_taxa_ids (set): Set of already written taxa IDs to avoid duplication.
        collection_records (QuerySet): Filtered collection records
        park_field_map (dict): {park_name: field_key} for dynamic invasion status columns
    """
    if park_field_map is None:
        park_field_map = {}

    unique_taxonomy_ids = set(record_taxonomy_ids) - written_taxa_ids

    if unique_taxonomy_ids:
        taxa = Taxonomy.objects.filter(
            id__in=unique_taxonomy_ids
        ).order_by('scientific_name')
        taxon_serializer = ChecklistSerializer(
            taxa,
            many=True,
            context={
                'collection_records': collection_records
            }
        )

        taxa_list = list(taxa)
        serializer_data = list(taxon_serializer.data)

        for taxon_obj, taxon in zip(taxa_list, serializer_data):
            written_taxa_ids.add(taxon['id'])
            row = dict(taxon)
            del row['id']

            if park_field_map and preferences.SiteSetting.project_name == 'sanparks':
                park_statuses = _get_invasion_status_for_taxon_parks(
                    taxon_obj,
                    park_field_map,
                    collection_records,
                )
                row.update(park_statuses)

            writer.writerow(row)


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
