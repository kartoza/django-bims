import csv
import os
from datetime import datetime
from django.conf import settings
from django.db.models import F
from django.http import Http404
from preferences import preferences
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape, letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm, inch, mm
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.platypus import (
    BaseDocTemplate, SimpleDocTemplate, TableStyle, Table, Spacer,
    Image, PageTemplate, Frame, PageBreak, KeepTogether, HRFlowable
)
from reportlab.platypus.para import Paragraph
from reportlab.graphics.shapes import Drawing, Rect, String, Line
from reportlab.graphics.charts.piecharts import Pie
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
                'navbar_logo_path': theme.navbar_logo.path if theme.navbar_logo else None,
            }
    except Exception:
        pass
    return {
        'primary': '#18A090',
        'secondary': '#DBAF00',
        'text': '#FFFFFF',
        'site_name': 'BIMS',
        'logo_path': None,
        'navbar_logo_path': None,
    }


class ChecklistPDFTemplate(BaseDocTemplate):
    """Custom PDF template with branded headers and footers."""

    def __init__(self, filename, theme, module_name, species_count, site_domain, **kwargs):
        self.theme = theme
        self.module_name = module_name
        self.species_count = species_count
        self.site_domain = site_domain
        self.primary_color = colors.HexColor(theme['primary'])
        self.secondary_color = colors.HexColor(theme['secondary'])
        super().__init__(filename, **kwargs)

    def afterPage(self):
        """Called after each page is created."""
        pass

    def handle_pageBegin(self):
        """Handle page begin - reset for new page."""
        self._handle_pageBegin()

    def _add_header_footer(self, canvas, doc):
        """Add header and footer to each page."""
        canvas.saveState()

        page_width, page_height = landscape(A4)

        # Header bar
        canvas.setFillColor(self.primary_color)
        canvas.rect(0, page_height - 40, page_width, 40, fill=1, stroke=0)

        # Header text
        canvas.setFillColor(colors.white)
        canvas.setFont('Helvetica-Bold', 12)
        header_text = f"{self.theme['site_name']} | {self.module_name} Species Checklist"
        canvas.drawString(20, page_height - 26, header_text)

        # Page number on right side of header
        canvas.setFont('Helvetica', 10)
        page_num_text = f"Page {doc.page}"
        canvas.drawRightString(page_width - 20, page_height - 26, page_num_text)

        # Footer bar
        canvas.setFillColor(colors.Color(0.95, 0.95, 0.95))
        canvas.rect(0, 0, page_width, 30, fill=1, stroke=0)

        # Footer line
        canvas.setStrokeColor(self.primary_color)
        canvas.setLineWidth(2)
        canvas.line(0, 30, page_width, 30)

        # Footer text
        canvas.setFillColor(colors.Color(0.4, 0.4, 0.4))
        canvas.setFont('Helvetica', 8)
        generated_text = f"Generated on {datetime.now().strftime('%d %B %Y at %H:%M')} | {self.site_domain}"
        canvas.drawString(20, 10, generated_text)

        # Species count on right
        canvas.drawRightString(page_width - 20, 10, f"Total Species: {self.species_count}")

        canvas.restoreState()

    def build_cover_page(self, story):
        """Build an elegant cover page."""
        page_width, page_height = landscape(A4)

        # Create styles
        styles = getSampleStyleSheet()

        # Add spacer for top margin
        story.append(Spacer(1, 2 * cm))

        # Logo if available
        logo_path = self.theme.get('logo_path') or self.theme.get('navbar_logo_path')
        if logo_path and os.path.exists(logo_path):
            try:
                logo = Image(logo_path, width=3*cm, height=3*cm)
                logo.hAlign = 'CENTER'
                story.append(logo)
                story.append(Spacer(1, 1 * cm))
            except Exception:
                pass

        # Site name
        site_style = ParagraphStyle(
            'SiteName',
            parent=styles['Heading1'],
            fontSize=14,
            textColor=colors.Color(0.4, 0.4, 0.4),
            alignment=TA_CENTER,
            spaceAfter=6,
            fontName='Helvetica',
            textTransform='uppercase',
            letterSpacing=3,
        )
        story.append(Paragraph(self.theme['site_name'], site_style))

        # Decorative line
        story.append(Spacer(1, 0.3 * cm))
        line = HRFlowable(
            width="30%",
            thickness=2,
            color=self.primary_color,
            spaceBefore=0,
            spaceAfter=0,
            hAlign='CENTER'
        )
        story.append(line)
        story.append(Spacer(1, 0.5 * cm))

        # Main title
        title_style = ParagraphStyle(
            'CoverTitle',
            parent=styles['Heading1'],
            fontSize=36,
            textColor=self.primary_color,
            alignment=TA_CENTER,
            spaceAfter=12,
            fontName='Helvetica-Bold',
            leading=42,
        )
        story.append(Paragraph("Species Checklist", title_style))

        # Module name as subtitle
        subtitle_style = ParagraphStyle(
            'CoverSubtitle',
            parent=styles['Heading2'],
            fontSize=24,
            textColor=colors.Color(0.3, 0.3, 0.3),
            alignment=TA_CENTER,
            spaceAfter=30,
            fontName='Helvetica',
        )
        story.append(Paragraph(self.module_name, subtitle_style))

        story.append(Spacer(1, 1 * cm))

        # Stats box
        stats_data = [
            [
                Paragraph(f'<font size="28" color="#{self.theme["primary"][1:]}">{self.species_count}</font>', styles['Normal']),
            ],
            [
                Paragraph('<font size="10" color="#666666">Species Recorded</font>', styles['Normal']),
            ]
        ]
        stats_table = Table(stats_data, colWidths=[4*cm])
        stats_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('BOX', (0, 0), (-1, -1), 1, self.primary_color),
            ('TOPPADDING', (0, 0), (-1, -1), 15),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 15),
            ('LEFTPADDING', (0, 0), (-1, -1), 20),
            ('RIGHTPADDING', (0, 0), (-1, -1), 20),
        ]))
        stats_table.hAlign = 'CENTER'
        story.append(stats_table)

        story.append(Spacer(1, 2 * cm))

        # Generation date
        date_style = ParagraphStyle(
            'CoverDate',
            parent=styles['Normal'],
            fontSize=11,
            textColor=colors.Color(0.5, 0.5, 0.5),
            alignment=TA_CENTER,
            fontName='Helvetica',
        )
        generated_date = datetime.now().strftime('%d %B %Y')
        story.append(Paragraph(f"Generated on {generated_date}", date_style))

        story.append(Spacer(1, 0.5 * cm))

        # Domain
        domain_style = ParagraphStyle(
            'CoverDomain',
            parent=styles['Normal'],
            fontSize=9,
            textColor=colors.Color(0.6, 0.6, 0.6),
            alignment=TA_CENTER,
            fontName='Helvetica',
        )
        story.append(Paragraph(self.site_domain, domain_style))

        # Page break after cover
        story.append(PageBreak())

        return story

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
    """Generate a beautifully formatted PDF species checklist."""
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
    secondary_color = colors.HexColor(theme['secondary'])
    text_color = colors.HexColor(theme['text'])

    written_taxa_ids = set()
    all_taxa = []
    common_names_and_count = {}
    threat_status_counts = {}

    taxonomy_collection_records = (
        collection_records.distinct(
            'taxonomy__scientific_name'
        ).order_by('taxonomy__scientific_name')
    )
    taxonomy_collection_records_count = taxonomy_collection_records.count()
    taxonomy_ids = list(taxonomy_collection_records.values_list('taxonomy_id', flat=True))

    # Create custom styles
    styles = getSampleStyleSheet()

    # Scientific name style (italic)
    scientific_style = ParagraphStyle(
        'Scientific',
        parent=styles['Normal'],
        fontSize=9,
        leading=12,
        fontName='Helvetica-Oblique',
        textColor=colors.Color(0.2, 0.2, 0.2),
    )

    # Common name style
    common_style = ParagraphStyle(
        'Common',
        parent=styles['Normal'],
        fontSize=9,
        leading=12,
        fontName='Helvetica',
        textColor=colors.Color(0.3, 0.3, 0.3),
    )

    # Status style with color coding potential
    status_style = ParagraphStyle(
        'Status',
        parent=styles['Normal'],
        fontSize=8,
        leading=11,
        fontName='Helvetica',
        alignment=TA_CENTER,
    )

    # Source style (smaller)
    source_style = ParagraphStyle(
        'Source',
        parent=styles['Normal'],
        fontSize=7,
        leading=10,
        fontName='Helvetica',
        textColor=colors.Color(0.5, 0.5, 0.5),
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

                # Track threat status for summary
                status = taxon['threat_status'] or 'Not Evaluated'
                threat_status_counts[status] = threat_status_counts.get(status, 0) + 1

                # Color code threat status
                status_color = colors.Color(0.4, 0.4, 0.4)  # Default gray
                status_text = taxon['threat_status'] or '-'
                if 'Critically' in status_text or 'CR' in status_text:
                    status_color = colors.HexColor('#D32F2F')  # Red
                elif 'Endangered' in status_text or 'EN' in status_text:
                    status_color = colors.HexColor('#F57C00')  # Orange
                elif 'Vulnerable' in status_text or 'VU' in status_text:
                    status_color = colors.HexColor('#FBC02D')  # Yellow
                elif 'Near Threatened' in status_text or 'NT' in status_text:
                    status_color = colors.HexColor('#7CB342')  # Light green
                elif 'Least Concern' in status_text or 'LC' in status_text:
                    status_color = colors.HexColor('#388E3C')  # Green

                status_para_style = ParagraphStyle(
                    'StatusColored',
                    parent=status_style,
                    textColor=status_color,
                    fontName='Helvetica-Bold',
                )

                taxon_entry = [
                    Paragraph(taxon['scientific_name'], scientific_style),
                    Paragraph(taxon['common_name'] or '-', common_style),
                    Paragraph(status_text, status_para_style),
                    Paragraph(taxon['sources'] or '-', source_style)
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

    # Generate the PDF with branded template
    species_count = len(all_taxa)
    page_width, page_height = landscape(A4)

    # Create custom document with header/footer
    doc = ChecklistPDFTemplate(
        pdf_file_path,
        theme=theme,
        module_name=module_name or 'All Taxa',
        species_count=species_count,
        site_domain=site_domain_name,
        pagesize=landscape(A4),
        topMargin=50,  # Space for header
        bottomMargin=40,  # Space for footer
        leftMargin=20,
        rightMargin=20
    )

    # Create frame for content
    content_frame = Frame(
        20, 40,  # x, y from bottom-left
        page_width - 40,  # width
        page_height - 90,  # height (leaving room for header/footer)
        id='content'
    )

    # Create page template with header/footer callback
    template = PageTemplate(
        id='checklist',
        frames=[content_frame],
        onPage=doc._add_header_footer
    )
    doc.addPageTemplates([template])

    elements = []

    # Build cover page
    doc.build_cover_page(elements)

    # Add summary section before the table
    summary_title_style = ParagraphStyle(
        'SummaryTitle',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=primary_color,
        spaceAfter=12,
        spaceBefore=6,
    )
    elements.append(Paragraph("Conservation Status Summary", summary_title_style))

    # Create summary table for threat status distribution
    if threat_status_counts:
        summary_data = []
        status_order = ['Critically Endangered', 'Endangered', 'Vulnerable',
                       'Near Threatened', 'Least Concern', 'Data Deficient', 'Not Evaluated']

        for status in status_order:
            count = threat_status_counts.get(status, 0)
            if count > 0:
                # Determine color
                if 'Critically' in status:
                    color_hex = '#D32F2F'
                elif status == 'Endangered':
                    color_hex = '#F57C00'
                elif status == 'Vulnerable':
                    color_hex = '#FBC02D'
                elif 'Near' in status:
                    color_hex = '#7CB342'
                elif 'Least' in status:
                    color_hex = '#388E3C'
                else:
                    color_hex = '#757575'

                status_style_sum = ParagraphStyle(
                    f'Status_{status}',
                    fontSize=9,
                    textColor=colors.HexColor(color_hex),
                    fontName='Helvetica-Bold',
                )
                summary_data.append([
                    Paragraph(status, status_style_sum),
                    Paragraph(str(count), ParagraphStyle('Count', fontSize=9, alignment=TA_RIGHT)),
                ])

        # Add any remaining statuses not in the order
        for status, count in threat_status_counts.items():
            if status not in status_order and count > 0:
                summary_data.append([
                    Paragraph(status, ParagraphStyle('StatusOther', fontSize=9)),
                    Paragraph(str(count), ParagraphStyle('Count', fontSize=9, alignment=TA_RIGHT)),
                ])

        if summary_data:
            summary_table = Table(summary_data, colWidths=[6*cm, 2*cm])
            summary_table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (0, -1), 'LEFT'),
                ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
                ('TOPPADDING', (0, 0), (-1, -1), 4),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                ('LINEBELOW', (0, 0), (-1, -2), 0.5, colors.Color(0.9, 0.9, 0.9)),
                ('LINEBELOW', (0, -1), (-1, -1), 1, primary_color),
            ]))
            elements.append(summary_table)

    elements.append(Spacer(1, 1 * cm))

    # Section title for species list
    list_title_style = ParagraphStyle(
        'ListTitle',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=primary_color,
        spaceAfter=12,
    )
    elements.append(Paragraph("Species List", list_title_style))

    # Create header style for table
    header_cell_style = ParagraphStyle(
        'HeaderCell',
        fontSize=9,
        textColor=colors.white,
        fontName='Helvetica-Bold',
        alignment=TA_LEFT,
    )

    # Build data table with styled header
    header_row = [
        Paragraph('Scientific Name', header_cell_style),
        Paragraph('Common Name', header_cell_style),
        Paragraph('Status', ParagraphStyle('HeaderCenter', parent=header_cell_style, alignment=TA_CENTER)),
        Paragraph('Data Sources', header_cell_style),
    ]
    data = [header_row] + all_taxa

    # Calculate column widths
    available_width = page_width - 40  # Account for margins
    col_widths = [
        available_width * 0.30,  # Scientific name
        available_width * 0.28,  # Common name
        available_width * 0.14,  # Status
        available_width * 0.28,  # Sources
    ]

    # Create table with professional styling
    table = Table(data, colWidths=col_widths, repeatRows=1)
    table.setStyle(TableStyle([
        # Header styling
        ('BACKGROUND', (0, 0), (-1, 0), primary_color),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
        ('TOPPADDING', (0, 0), (-1, 0), 10),

        # Content styling
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('TOPPADDING', (0, 1), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),

        # Alignment
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('ALIGN', (2, 0), (2, -1), 'CENTER'),  # Status column centered
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),

        # Borders
        ('BOX', (0, 0), (-1, -1), 1.5, primary_color),
        ('LINEBELOW', (0, 0), (-1, 0), 1.5, primary_color),
        ('LINEBELOW', (0, 1), (-1, -2), 0.5, colors.Color(0.85, 0.85, 0.85)),

        # Alternating row colors
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.Color(0.97, 0.97, 0.97)]),
    ]))

    elements.append(table)

    # Build the document
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
