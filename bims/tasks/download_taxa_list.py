# coding=utf-8
import csv
import datetime
import json
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
    CITES_LISTING, FADA_ID, ON_GBIF, GBIF_LINK
)
from bims.utils.domain import get_current_domain

logger = logging.getLogger(__name__)


def process_download_csv_taxa_list(request, csv_file_path, filename, user_id, download_request_id=''):
    import csv
    from django.contrib.auth import get_user_model
    from django.conf import settings

    from bims.api_views.taxon import TaxaList
    from bims.views.download_csv_taxa_list import TaxaCSVSerializer
    from bims.tasks import send_csv_via_email
    from bims.models.download_request import DownloadRequest
    from bims.scripts.species_keys import BIOGRAPHIC_DISTRIBUTIONS
    from bims.models.taxon_group import TaxonGroup
    from bims.models import TaxonGroupCitation
    from bims.templatetags import is_fada_site

    is_fada = is_fada_site()

    # FADA-only additional_data keys (column names)
    FADA_ADDITIONAL_KEYS = [
        'Taxonomic Comments',
        'Taxonomic References',
        'Biogeographic Comments',
        'Biogeographic References',
        'Environmental Comments',
        'Environmental References',
        'Conservation Comments',
        'Conservation References',
    ]

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
            from bims.utils import get_current_domain
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

    taxa_qs = TaxaList.get_taxa_by_parameters(request_get)
    try:
        taxa_qs = taxa_qs.prefetch_related('tags', 'biographic_distributions', 'vernacular_names')
    except Exception:
        pass

    total_taxa = taxa_qs.count()

    tag_titles = set()
    additional_attributes_titles = set()

    def update_headers(_headers):
        _updated_headers = []
        for header in _headers:
            if header in FADA_ADDITIONAL_KEYS:
                _updated_headers.append(header)
                continue
            original = header
            if header == 'class_name':
                header = CLASS
            elif header == 'taxon_rank':
                header = TAXON_RANK
            elif header == 'common_name':
                header = COMMON_NAME
            elif header == 'accepted_taxon':
                header = ACCEPTED_TAXON
            elif header == 'fada_id':
                header = FADA_ID
                _updated_headers.append(header)
                continue
            elif header.lower().strip() in ['on_gbif', 'on gbif']:
                header = ON_GBIF
                _updated_headers.append(header)
                continue
            elif header.lower().strip() in ['gbif_link', 'gbif link']:
                header = GBIF_LINK
                _updated_headers.append(header)
                continue

            header = header.replace('_or_', '/')

            if (
                not header.istitle()
                and original not in tag_titles
                and original not in additional_attributes_titles
            ):
                header = header.replace('_', ' ').capitalize()
            if header == 'Subspecies':
                header = SUBSPECIES
            if header.lower().strip() == 'cites_listing':
                header = CITES_LISTING

            _updated_headers.append(header)
        return _updated_headers

    raw_headers = []
    for taxon in taxa_qs.iterator():
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

    updated_headers = update_headers(raw_headers)

    progress = 1
    with open(csv_file_path, 'w', newline='') as csv_file:
        writer = csv.writer(csv_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)

        writer.writerow(updated_headers)

        taxa_qs_write = TaxaList.get_taxa_by_parameters(request_get)
        try:
            taxa_qs_write = taxa_qs_write.prefetch_related('tags', 'biographic_distributions', 'vernacular_names')
        except Exception:
            pass

        for taxon in taxa_qs_write.iterator():
            ser = TaxaCSVSerializer(taxon)
            row = ser.data

            if is_fada:
                for k in FADA_ADDITIONAL_KEYS:
                    if k not in row:
                        row[k] = _from_additional_data(taxon, k)

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


def process_download_pdf_taxa_list(
        request, pdf_file_path, filename, user_id, taxon_group_id, download_request_id):
    from bims.tasks import send_csv_via_email
    from bims.models.taxon_group import TaxonGroup
    from bims.api_views.taxon import TaxaList
    from bims.models import TaxonGroupCitation

    class RequestGet:
        def __init__(self, get_data, user=None):
            self.GET = get_data
            self.user = user

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

        heading_style = ParagraphStyle(
            name="HeadingStyle", parent=styles['Normal'],
            fontName='Times-Bold', fontSize=12, leading=14, alignment=TA_LEFT,
        )
        citation_style = ParagraphStyle(
            name="CitationStyle", parent=styles['Normal'],
            fontName='Times-Roman', fontSize=10, leading=12, alignment=TA_LEFT,
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

        # --- Citations ---
        citations = (
            TaxonGroupCitation.objects
            .filter(taxon_group=taxon_group)
            .order_by('-year', '-access_date', '-updated_at', '-created_at')
        )
        if citations.exists():
            paragraphs.append(Paragraph("To be cited as:", heading_style))
            for c in citations:
                paragraphs.append(Paragraph(c.formatted_citation, citation_style))
            paragraphs.append(Spacer(1, 12))
        else:
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

    UserModel = get_user_model()
    user = None
    if user_id:
        try:
            user = UserModel.objects.get(id=user_id)
        except UserModel.DoesNotExist:
            pass

    request_get = RequestGet(request, user)
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
