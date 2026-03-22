# coding=utf-8
import csv
import datetime
import json
import logging
import os
from django.conf import settings
from django.contrib.auth import get_user_model
from celery import shared_task
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    Paragraph, Spacer, SimpleDocTemplate, BaseDocTemplate,
    PageTemplate, Frame, PageBreak, Image, HRFlowable
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase.pdfmetrics import registerFontFamily

from bims.scripts.species_keys import (
    ACCEPTED_TAXON, TAXON_RANK,
    COMMON_NAME, CLASS, SUBSPECIES,
    CITES_LISTING, FADA_ID, ON_GBIF, GBIF_LINK,
    SPECIES_GROUP, SUBGENUS, SUBTRIBE, SUBFAMILY,
    SUBORDER, SUBCLASS, SUBPHYLUM, SPECIES, GENUS,
    TRIBE, FAMILY, ORDER, PHYLUM, KINGDOM, AUTHORS
)
from bims.utils.domain import get_current_domain

logger = logging.getLogger(__name__)


def process_download_csv_taxa_list(
        request,
        csv_file_path,
        filename,
        user_id,
        download_request_id='',
        taxa_ids=None,
        order_by=None
    ):
    import csv
    from django.contrib.auth import get_user_model
    from django.conf import settings

    from bims.api_views.taxon import TaxaList
    from bims.views.download_csv_taxa_list import (
        TaxaCSVSerializer,
        is_sanparks_project,
        NATIONAL_NEMBA_LABEL,
    )
    from bims.tasks import send_csv_via_email
    from bims.models.download_request import DownloadRequest
    from bims.scripts.species_keys import BIOGRAPHIC_DISTRIBUTIONS
    from bims.models.taxon_group import TaxonGroup
    from bims.models import TaxonGroupCitation
    from bims.templatetags import is_fada_site
    from bims.fada.taxa_list import (
        FADA_ADDITIONAL_KEYS,
        reorder_headers_for_fada,
    )

    is_fada = is_fada_site()
    sanparks_project = is_sanparks_project()

    def _from_additional_data(instance, k):
        data = getattr(instance, 'additional_data', None)
        if not data:
            return ''
        if isinstance(data, dict):
            return data.get(k, '')
        try:
            parsed = json.loads(data)
            if isinstance(parsed, dict):
                return parsed.get(k, '')
        except Exception:
            pass
        return ''

    def _current_domain():
        try:
            from bims.utils.domain import get_current_domain
            return get_current_domain()
        except Exception:  # noqa
            pass
        try:
            from django.contrib.sites.models import Site
            return Site.objects.get_current().domain
        except Exception:  # noqa
            pass
        return getattr(settings, "SITE_DOMAIN", "")

    class RequestGet:
        def __init__(self, get_data, user=None):
            self.GET = get_data
            self.user = user

    User = get_user_model()
    user = None
    if user_id:
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            pass

    request_get = RequestGet(request, user)

    taxon_group_name = "Taxa checklist"
    tg_id = request.get("taxonGroup") if isinstance(request, dict) else None
    if tg_id:
        try:
            tg = TaxonGroup.objects.get(id=tg_id)
            taxon_group_name = f"{tg.name} checkList"
        except TaxonGroup.DoesNotExist:
            pass

    if taxa_ids:
        from bims.models import Taxonomy
        taxa_qs = Taxonomy.objects.filter(id__in=taxa_ids)
        if order_by:
            taxa_qs = taxa_qs.order_by(order_by)
        if is_fada:
            from django.db.models import Q
            taxa_qs = taxa_qs.exclude(Q(fada_id__isnull=True) | Q(fada_id=''))
    else:
        taxa_qs = TaxaList.get_taxa_by_parameters(request_get)
    try:
        taxa_qs = taxa_qs.prefetch_related('tags', 'biographic_distributions', 'vernacular_names')
    except Exception:
        pass

    total_taxa = taxa_qs.count()

    tag_titles = set()
    additional_attributes_titles = set()

    def update_headers(_headers):
        header_map = {
            'class_name': CLASS,
            'taxon_rank': TAXON_RANK,
            'common_name': COMMON_NAME,
            'accepted_taxon': ACCEPTED_TAXON,
            'fada_id': FADA_ID,
            'species_group': SPECIES_GROUP,
            'subgenus': SUBGENUS,
            'subtribe': SUBTRIBE,
            'subfamily': SUBFAMILY,
            'suborder': SUBORDER,
            'subclass': SUBCLASS,
            'subphylum': SUBPHYLUM,
            'subspecies': SUBSPECIES,
            'species': SPECIES,
            'genus': GENUS,
            'tribe': TRIBE,
            'family': FAMILY,
            'order': ORDER,
            'phylum': PHYLUM,
            'kingdom': KINGDOM,
            'cites_listing': CITES_LISTING,
            'author': AUTHORS,
            'taxonomic_status': 'Taxonomic Status',
        }

        _updated_headers = []
        for header in _headers:
            if header in FADA_ADDITIONAL_KEYS:
                _updated_headers.append(header)
                continue
            original = header

            if header.lower() in header_map:
                header = header_map[header.lower()]
                _updated_headers.append(header)
                continue

            if header.lower().strip() in ['on_gbif', 'on gbif']:
                header = ON_GBIF
                _updated_headers.append(header)
                continue
            elif header.lower().strip() in ['gbif_link', 'gbif link']:
                header = GBIF_LINK
                _updated_headers.append(header)
                continue
            elif header.lower().strip() == 'invasion':
                header = NATIONAL_NEMBA_LABEL if sanparks_project else 'Invasion'
                _updated_headers.append(header)
                continue

            header = header.replace('_or_', '/')

            if (
                not header.istitle()
                and original not in tag_titles
                and original not in additional_attributes_titles
            ):
                header = header.replace('_', ' ').capitalize()

            _updated_headers.append(header)
        return _updated_headers

    raw_headers = []
    for taxon in taxa_qs.iterator(chunk_size=2000):
        ser = TaxaCSVSerializer(taxon)
        row = ser.data

        for k in row.keys():
            if k not in raw_headers:
                raw_headers.append(k)

        tag_titles.update(ser.context.get('tags', []))
        additional_attributes_titles.update(
            ser.context.get('additional_attributes_titles', [])
        )

    for key in BIOGRAPHIC_DISTRIBUTIONS:
        if key not in raw_headers:
            raw_headers.append(key)

    if is_fada:
        for k in FADA_ADDITIONAL_KEYS:
            if k not in raw_headers:
                raw_headers.append(k)
        raw_headers = reorder_headers_for_fada(raw_headers)

    if taxa_ids:
        raw_headers.append('admin_url')

    updated_headers = update_headers(raw_headers)

    progress = 1
    with open(csv_file_path, 'w', newline='') as csv_file:
        writer = csv.writer(csv_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)

        writer.writerow(updated_headers)

        if taxa_ids:
            taxa_qs_write = Taxonomy.objects.filter(id__in=taxa_ids)
            if order_by:
                taxa_qs_write = taxa_qs_write.order_by(order_by)
            if is_fada:
                from django.db.models import Q
                taxa_qs_write = taxa_qs_write.exclude(Q(fada_id__isnull=True) | Q(fada_id=''))
        else:
            taxa_qs_write = TaxaList.get_taxa_by_parameters(request_get)
        try:
            taxa_qs_write = taxa_qs_write.prefetch_related('tags', 'biographic_distributions', 'vernacular_names')
        except Exception:
            pass

        if taxa_ids:
            from django.urls import reverse
            current_domain = _current_domain()

        for taxon in taxa_qs_write.iterator(chunk_size=2000):
            ser = TaxaCSVSerializer(taxon)
            row = ser.data

            if is_fada:
                for k in FADA_ADDITIONAL_KEYS:
                    if k not in row:
                        row[k] = _from_additional_data(taxon, k)

            if taxa_ids:
                admin_path = reverse(
                    'admin:bims_taxonomy_change', args=[taxon.pk]
                )
                row['admin_url'] = f'{current_domain}{admin_path}'

            writer.writerow([row.get(k, '') for k in raw_headers])

            if progress % 10 == 0 and download_request_id:
                try:
                    download_request = DownloadRequest.objects.get(id=download_request_id)
                    download_request.progress = f'{progress}/{total_taxa}'
                    download_request.save(update_fields=['progress'])
                except DownloadRequest.DoesNotExist:
                    pass

            progress += 1

        writer.writerow([])

        # Metadata
        title_text = f"{taxon_group_name}"
        writer.writerow([title_text])
        current_site = _current_domain()
        generated_text = (
            f"(generated {datetime.datetime.now().strftime('%a %b %d %H:%M:%S %Y')} "
            f"from {current_site})"
        )
        writer.writerow([generated_text])

        # --- Citations ---
        try:
            if tg_id:
                tg = TaxonGroup.objects.get(id=tg_id)
                citations = (
                    TaxonGroupCitation.objects
                    .filter(taxon_group=tg)
                    .order_by('-year', '-access_date', '-updated_at', '-created_at')
                )
                if citations.exists():
                    writer.writerow([])  # spacer
                    writer.writerow(["To be cited as:"])
                    for c in citations:
                        writer.writerow([c.formatted_citation])
        except Exception:
            pass


    UserModel = get_user_model()
    try:
        user = UserModel.objects.get(id=user_id)
        if download_request_id:
            DownloadRequest.objects.filter(id=download_request_id).update(
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


class TaxaListPDFTemplate(BaseDocTemplate):
    """Custom PDF template with branded headers and footers for taxa lists."""

    def __init__(self, filename, theme, taxon_group_name, species_count, site_domain, **kwargs):
        self.theme = theme
        self.taxon_group_name = taxon_group_name
        self.species_count = species_count
        self.site_domain = site_domain
        self.primary_color = colors.HexColor(theme['primary'])
        self.secondary_color = colors.HexColor(theme['secondary'])
        super().__init__(filename, **kwargs)

    def _add_header_footer(self, canvas, doc):
        """Add header and footer to each page."""
        canvas.saveState()

        page_width, page_height = A4

        # Header bar
        canvas.setFillColor(self.primary_color)
        canvas.rect(0, page_height - 35, page_width, 35, fill=1, stroke=0)

        # Header text
        canvas.setFillColor(colors.white)
        canvas.setFont('Helvetica-Bold', 10)
        header_text = f"{self.theme['site_name']} | {self.taxon_group_name} Taxa List"
        canvas.drawString(20, page_height - 23, header_text)

        # Page number on right side of header
        canvas.setFont('Helvetica', 9)
        page_num_text = f"Page {doc.page}"
        canvas.drawRightString(page_width - 20, page_height - 23, page_num_text)

        # Footer bar
        canvas.setFillColor(colors.Color(0.95, 0.95, 0.95))
        canvas.rect(0, 0, page_width, 25, fill=1, stroke=0)

        # Footer line
        canvas.setStrokeColor(self.primary_color)
        canvas.setLineWidth(2)
        canvas.line(0, 25, page_width, 25)

        # Footer text
        canvas.setFillColor(colors.Color(0.4, 0.4, 0.4))
        canvas.setFont('Helvetica', 7)
        generated_text = f"Generated on {datetime.datetime.now().strftime('%d %B %Y at %H:%M')} | {self.site_domain}"
        canvas.drawString(20, 8, generated_text)

        # Species count on right
        canvas.drawRightString(page_width - 20, 8, f"Total Species: {self.species_count}")

        canvas.restoreState()

    def build_cover_page(self, story):
        """Build an elegant cover page."""
        page_width, page_height = A4
        styles = getSampleStyleSheet()

        # Add spacer for top margin
        story.append(Spacer(1, 3 * cm))

        # Logo if available
        logo_path = self.theme.get('logo_path') or self.theme.get('navbar_logo_path')
        if logo_path and os.path.exists(logo_path):
            try:
                logo = Image(logo_path, width=2.5*cm, height=2.5*cm)
                logo.hAlign = 'CENTER'
                story.append(logo)
                story.append(Spacer(1, 1 * cm))
            except Exception:
                pass

        # Site name
        site_style = ParagraphStyle(
            'SiteName',
            parent=styles['Heading1'],
            fontSize=12,
            textColor=colors.Color(0.4, 0.4, 0.4),
            alignment=TA_CENTER,
            spaceAfter=6,
            fontName='Helvetica',
        )
        story.append(Paragraph(self.theme['site_name'].upper(), site_style))

        # Decorative line
        story.append(Spacer(1, 0.3 * cm))
        line = HRFlowable(
            width="25%",
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
            fontSize=32,
            textColor=self.primary_color,
            alignment=TA_CENTER,
            spaceAfter=12,
            fontName='Helvetica-Bold',
            leading=38,
        )
        story.append(Paragraph("Taxa List", title_style))

        # Taxon group name as subtitle
        subtitle_style = ParagraphStyle(
            'CoverSubtitle',
            parent=styles['Heading2'],
            fontSize=22,
            textColor=colors.Color(0.3, 0.3, 0.3),
            alignment=TA_CENTER,
            spaceAfter=30,
            fontName='Helvetica',
        )
        story.append(Paragraph(self.taxon_group_name, subtitle_style))

        story.append(Spacer(1, 1.5 * cm))

        # Species count box
        count_style = ParagraphStyle(
            'CountStyle',
            fontSize=24,
            textColor=self.primary_color,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold',
        )
        label_style = ParagraphStyle(
            'LabelStyle',
            fontSize=10,
            textColor=colors.Color(0.5, 0.5, 0.5),
            alignment=TA_CENTER,
            fontName='Helvetica',
        )
        story.append(Paragraph(str(self.species_count), count_style))
        story.append(Paragraph("Species Recorded", label_style))

        story.append(Spacer(1, 2 * cm))

        # Generation date
        date_style = ParagraphStyle(
            'CoverDate',
            parent=styles['Normal'],
            fontSize=10,
            textColor=colors.Color(0.5, 0.5, 0.5),
            alignment=TA_CENTER,
            fontName='Helvetica',
        )
        generated_date = datetime.datetime.now().strftime('%d %B %Y')
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


def process_download_pdf_taxa_list(
        request, pdf_file_path, filename, user_id, taxon_group_id, download_request_id):
    """Generate a professionally styled PDF taxa list."""
    from bims.tasks import send_csv_via_email
    from bims.models.taxon_group import TaxonGroup
    from bims.api_views.taxon import TaxaList
    from bims.models import TaxonGroupCitation

    class RequestGet:
        def __init__(self, get_data, user=None):
            self.GET = get_data
            self.user = user

    # Get theme and site info
    theme = get_theme_colors()
    site_domain = get_current_domain()
    primary_color = colors.HexColor(theme['primary'])

    # Register Garamond fonts if available
    try:
        font_dir = os.path.join(settings.STATIC_ROOT, 'fonts', 'garamond')
        if os.path.exists(os.path.join(font_dir, 'EBGaramond-Regular.ttf')):
            pdfmetrics.registerFont(TTFont('Garamond', os.path.join(font_dir, 'EBGaramond-Regular.ttf')))
            pdfmetrics.registerFont(TTFont('Garamond-Bold', os.path.join(font_dir, 'EBGaramond-Bold.ttf')))
            pdfmetrics.registerFont(TTFont('Garamond-Italic', os.path.join(font_dir, 'EBGaramond-Italic.ttf')))
            pdfmetrics.registerFont(TTFont('Garamond-BoldItalic', os.path.join(font_dir, 'EBGaramond-BoldItalic.ttf')))
            registerFontFamily(
                'Garamond',
                normal='Garamond',
                bold='Garamond-Bold',
                italic='Garamond-Italic',
                boldItalic='Garamond-BoldItalic'
            )
            body_font = 'Garamond'
            body_font_bold = 'Garamond-Bold'
            body_font_italic = 'Garamond-Italic'
        else:
            body_font = 'Helvetica'
            body_font_bold = 'Helvetica-Bold'
            body_font_italic = 'Helvetica-Oblique'
    except Exception:
        body_font = 'Helvetica'
        body_font_bold = 'Helvetica-Bold'
        body_font_italic = 'Helvetica-Oblique'

    taxon_group = TaxonGroup.objects.get(id=taxon_group_id)

    UserModel = get_user_model()
    user = None
    if user_id:
        try:
            user = UserModel.objects.get(id=user_id)
        except UserModel.DoesNotExist:
            pass

    request_get = RequestGet(request, user)
    taxonomies = TaxaList.get_taxa_by_parameters(request_get)

    # Count species for the cover page
    species_qs = taxonomies.filter(rank__in=['SPECIES', 'SUBSPECIES'])
    species_count = species_qs.count()

    # Create styled paragraph styles
    styles = getSampleStyleSheet()

    genus_style = ParagraphStyle(
        name="GenusStyle",
        parent=styles['Normal'],
        fontName=body_font_bold,
        fontSize=12,
        leading=16,
        textColor=primary_color,
        spaceBefore=12,
        spaceAfter=4,
    )

    species_style = ParagraphStyle(
        name="SpeciesStyle",
        parent=styles['Normal'],
        fontName=body_font,
        fontSize=10,
        leading=14,
        leftIndent=20,
        textColor=colors.Color(0.2, 0.2, 0.2),
    )

    heading_style = ParagraphStyle(
        name="HeadingStyle",
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=14,
        leading=18,
        textColor=primary_color,
        spaceBefore=20,
        spaceAfter=10,
    )

    citation_style = ParagraphStyle(
        name="CitationStyle",
        parent=styles['Normal'],
        fontName=body_font_italic,
        fontSize=9,
        leading=12,
        textColor=colors.Color(0.4, 0.4, 0.4),
        leftIndent=10,
    )

    # Build page dimensions
    page_width, page_height = A4

    # Create custom document with header/footer
    doc = TaxaListPDFTemplate(
        pdf_file_path,
        theme=theme,
        taxon_group_name=taxon_group.name,
        species_count=species_count,
        site_domain=site_domain,
        pagesize=A4,
        topMargin=45,
        bottomMargin=35,
        leftMargin=50,
        rightMargin=50
    )

    # Create frame for content
    content_frame = Frame(
        50, 35,
        page_width - 100,
        page_height - 80,
        id='content'
    )

    # Create page template with header/footer callback
    template = PageTemplate(
        id='taxalist',
        frames=[content_frame],
        onPage=doc._add_header_footer
    )
    doc.addPageTemplates([template])

    story = []

    # Build cover page
    doc.build_cover_page(story)

    # Add citations section if available
    citations = (
        TaxonGroupCitation.objects
        .filter(taxon_group=taxon_group)
        .order_by('-year', '-access_date', '-updated_at', '-created_at')
    )
    if citations.exists():
        story.append(Paragraph("Citation", heading_style))
        for c in citations:
            story.append(Paragraph(c.formatted_citation, citation_style))
        story.append(Spacer(1, 1 * cm))

    # Add species list section header
    story.append(Paragraph("Species List", heading_style))

    # Build genus/species hierarchy
    genus_dict = {}
    species_qs_ordered = species_qs.order_by('canonical_name')

    for s in species_qs_ordered:
        genus = s.genus
        if not genus:
            continue
        if genus.id not in genus_dict:
            genus_dict[genus.id] = {
                'obj': genus,
                'species': []
            }
        genus_dict[genus.id]['species'].append(s)

    # Sort genera alphabetically
    sorted_genera = sorted(genus_dict.items(), key=lambda x: x[1]['obj'].canonical_name)

    for genus_id, info in sorted_genera:
        g_obj = info['obj']
        genus_line = f"<i>{g_obj.canonical_name}</i>"
        if g_obj.author and g_obj.author not in g_obj.canonical_name:
            genus_line += f" {g_obj.author}"

        story.append(Paragraph(genus_line, genus_style))

        for s_obj in sorted(info['species'], key=lambda x: x.canonical_name):
            sp_line = f"<i>{s_obj.canonical_name}</i>"
            if s_obj.author:
                sp_line += f" <font color='#666666'>{s_obj.author}</font>"
            if s_obj.additional_data and "type species" in s_obj.additional_data:
                sp_line += " <font color='#999999'>(Type species)</font>"

            story.append(Paragraph(sp_line, species_style))

    # Build the document
    doc.build(story)

    # Send via email
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
        request, csv_file, filename, user_id, output = 'csv', download_request_id='',
        taxon_group_id = None, taxa_ids=None, order_by=None):
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
                    request, csv_file, filename, user_id, download_request_id,
                    taxa_ids=taxa_ids, order_by=order_by
                )
            else:
                return process_download_pdf_taxa_list(
                    request, csv_file, filename, user_id, taxon_group_id, download_request_id
                )
    logger.info(
        'Csv %s is already being processed by another worker',
        csv_file)
