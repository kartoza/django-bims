# coding=utf-8
import io
import re
import zipfile
from datetime import datetime

from celery import shared_task
from celery.utils.log import get_task_logger

from bims.utils.domain import get_current_domain

logger = get_task_logger(__name__)


# ------------------------------------------------------------------ #
# Citation formatters
# ------------------------------------------------------------------ #

def _bibtex_authors(authors_str: str) -> str:
    """Normalise an author string to BibTeX's 'A and B and C' convention."""
    parts = [p.strip() for p in authors_str.replace('&', ',').split(',') if p.strip()]
    return ' and '.join(parts)


def _bibtex_key(ref):
    """Derive a simple BibTeX cite key: <surname><year><first-title-word>."""
    authors = ref.authors or ''
    first_author = authors.replace('&', ',').split(',')[0].strip()
    surname = first_author.split()[-1] if first_author else 'unknown'
    year = str(ref.year) if ref.year and str(ref.year) != '-' else 'nd'
    title = ref.title or ''
    first_word = title.split()[0].lower() if title and title != 'Unpublished data' else ''
    return re.sub(r'[^\w]', '', f'{surname}{year}{first_word}')


def _format_bibtex(ref):
    """Return a BibTeX entry string for a SourceReference."""
    key = _bibtex_key(ref)
    title = ref.title or ''
    authors = _bibtex_authors(ref.authors or '')
    year = ref.year

    entry_type = 'misc'
    extra_fields = {}

    if ref.is_bibliography():
        entry_type = 'article'
        try:
            bib = ref.sourcereferencebibliography
            if bib.source.journal:
                extra_fields['journal'] = bib.source.journal.name or ''
            if bib.source.doi:
                extra_fields['doi'] = bib.source.doi
            elif bib.source.url:
                extra_fields['url'] = bib.source.url
        except Exception:  # noqa
            pass
    elif ref.is_published_report():
        entry_type = 'techreport'
        try:
            src = ref.sourcereferencedocument.source
            url = src.doc_url or (src.doc_file.url if src.doc_file else '')
            if url:
                extra_fields['url'] = _absolute_url(url)
        except Exception:  # noqa
            pass
        institution = (
            ref.reference_source
            if ref.reference_source and ref.reference_source != '-'
            else authors or 'Unknown'
        )
        extra_fields['institution'] = institution
    elif ref.is_database():
        entry_type = 'misc'
        try:
            url = ref.sourcereferencedatabase.source.url or ''
            if url:
                extra_fields['url'] = _absolute_url(url)
        except Exception:  # noqa
            pass
    elif ref.note:
        entry_type = 'unpublished'

    fields = [f'  author = {{{authors}}}', f'  title = {{{title}}}']
    if year and str(year) != '-':
        fields.append(f'  year = {{{year}}}')
    for field_name, value in extra_fields.items():
        fields.append(f'  {field_name} = {{{value}}}')
    if entry_type == 'unpublished':
        note = ref.note if ref.note and ref.note != '-' else 'Unpublished data'
        fields.append(f'  note = {{{note}}}')

    body = ',\n'.join(fields)
    return f'@{entry_type}{{{key},\n{body}\n}}\n'


def _format_ris(ref):
    """Return an RIS entry string for a SourceReference."""
    lines = []

    if ref.is_bibliography():
        lines.append('TY  - JOUR')
    elif ref.is_published_report():
        lines.append('TY  - RPRT')
    elif ref.is_database():
        lines.append('TY  - DATA')
    else:
        lines.append('TY  - GEN')

    if ref.authors and ref.authors != '-':
        for author in ref.authors.replace('&', ',').split(','):
            a = author.strip()
            if a:
                lines.append(f'AU  - {a}')

    if ref.title:
        lines.append(f'TI  - {ref.title}')

    year = ref.year
    if year and str(year) != '-':
        lines.append(f'PY  - {year}')

    try:
        if ref.is_bibliography():
            bib = ref.sourcereferencebibliography
            if bib.source.journal:
                lines.append(f'JO  - {bib.source.journal.name}')
            if bib.source.doi:
                lines.append(f'DO  - {bib.source.doi}')
            elif bib.source.url:
                lines.append(f'UR  - {bib.source.url}')
    except Exception:  # noqa
        pass

    try:
        if ref.is_published_report():
            src = ref.sourcereferencedocument.source
            url = src.doc_url or (src.doc_file.url if src.doc_file else '')
            if url:
                lines.append(f'UR  - {_absolute_url(url)}')
    except Exception:  # noqa
        pass

    try:
        if ref.is_database():
            url = ref.sourcereferencedatabase.source.url or ''
            if url:
                lines.append(f'UR  - {_absolute_url(url)}')
    except Exception:  # noqa
        pass

    if ref.note and ref.note != '-':
        lines.append(f'N1  - {ref.note}')

    lines.append('ER  - ')
    return '\n'.join(lines) + '\n'


def _format_plain(ref):
    """Return an APA-style plain-text citation for a SourceReference."""
    authors = ref.authors if ref.authors and ref.authors != '-' else 'Unknown'
    year = ref.year if ref.year and str(ref.year) != '-' else 'n.d.'
    title = ref.title or 'Untitled'
    source = (
        ref.reference_source
        if ref.reference_source and ref.reference_source != '-' else ''
    )

    doi_url = ''
    try:
        if ref.is_bibliography():
            bib = ref.sourcereferencebibliography
            doi_url = bib.source.doi or bib.source.url or ''
        elif ref.is_published_report():
            src = ref.sourcereferencedocument.source
            doi_url = src.doc_url or (src.doc_file.url if src.doc_file else '')
            doi_url = _absolute_url(doi_url)
        elif ref.is_database():
            doi_url = ref.sourcereferencedatabase.source.url or ''
    except Exception:  # noqa
        pass

    parts = [f'{authors} ({year}). {title}.']
    if source:
        parts.append(f' {source}.')
    if doi_url:
        parts.append(f' {doi_url}')
    return ''.join(parts)


def _format_reference(ref, citation_format):
    if citation_format == 'bibtex':
        return _format_bibtex(ref)
    if citation_format == 'ris':
        return _format_ris(ref)
    return _format_plain(ref)


def _file_extension(citation_format):
    return {'bibtex': 'bib', 'ris': 'ris'}.get(citation_format, 'txt')


def _absolute_url(url: str) -> str:
    """Prefix a relative URL with the current tenant host."""
    if url and url.startswith('/'):
        return f'https://{get_current_domain()}{url}'
    return url


# ------------------------------------------------------------------ #
# Dataset (GBIF occurrence dataset) citation helpers
# ------------------------------------------------------------------ #

def _parse_dataset_author_year(dataset):
    """Extract author string and year from dataset.citation."""
    author, year = '', ''
    if dataset.citation:
        author_with_year = dataset.citation.split('.')[0]
        match = re.match(r'^(.*?)\s*\((\d{4})\)$', author_with_year)
        if match:
            author = match.group(1)
            year = match.group(2)
    return author, year


def _dataset_url(dataset):
    """Return a full URL, prefixing bare DOIs with https://doi.org/."""
    url = dataset.url or ''
    if url and url.startswith('10.'):
        return f'https://doi.org/{url}'
    return url


def _format_dataset_bibtex(dataset):
    author, year = _parse_dataset_author_year(dataset)
    # GBIF authors are "Lastname Initial" - take first token of first segment.
    first_segment = author.replace('&', ',').split(',')[0].strip()
    surname = first_segment.split()[0] if first_segment else 'unknown'
    author = _bibtex_authors(author)
    # Strip characters invalid in BibTeX keys (commas, spaces, dots, etc.)
    first_word = re.sub(r'[^\w]', '', dataset.name.split()[0].lower()) if dataset.name else ''
    key = re.sub(r'[^\w]', '', f'{surname}{year}{first_word}')
    fields = [f'  author = {{{author}}}', f'  title = {{{dataset.name}}}']
    if year:
        fields.append(f'  year = {{{year}}}')
    fields.append('  publisher = {Global Biodiversity Information Facility (GBIF)}')
    url = _dataset_url(dataset)
    if url:
        fields.append(f'  url = {{{url}}}')
    body = ',\n'.join(fields)
    return f'@misc{{{key},\n{body}\n}}\n'


def _format_dataset_ris(dataset):
    author, year = _parse_dataset_author_year(dataset)
    lines = ['TY  - DATA']
    if author:
        for a in author.replace('&', ',').split(','):
            a = a.strip()
            if a:
                lines.append(f'AU  - {a}')
    if dataset.name:
        lines.append(f'TI  - {dataset.name}')
    if year:
        lines.append(f'PY  - {year}')
    lines.append('PB  - Global Biodiversity Information Facility (GBIF)')
    raw_url = dataset.url or ''
    if raw_url.startswith('10.'):
        lines.append(f'DO  - {raw_url}')
    elif raw_url:
        lines.append(f'UR  - {raw_url}')
    lines.append('ER  - ')
    return '\n'.join(lines) + '\n'


def _format_dataset_plain(dataset):
    author, year = _parse_dataset_author_year(dataset)
    authors_str = author if author else 'Unknown'
    year_str = year if year else 'n.d.'
    parts = [f'{authors_str} ({year_str}). {dataset.name}.']
    parts.append(' Global Biodiversity Information Facility (GBIF).')
    url = _dataset_url(dataset)
    if url:
        parts.append(f' {url}')
    return ''.join(parts)


def _format_dataset(dataset, citation_format):
    if citation_format == 'bibtex':
        return _format_dataset_bibtex(dataset)
    if citation_format == 'ris':
        return _format_dataset_ris(dataset)
    return _format_dataset_plain(dataset)


# ------------------------------------------------------------------ #
# Celery task
# ------------------------------------------------------------------ #

@shared_task(name='bims.tasks.generate_citation_download', queue='search')
def generate_citation_download(
        download_request_id: int,
        source_reference_ids: list,
        citation_format: str,
        user_id: int,
        dataset_ids: list = None,
) -> str:
    """
    Format source references and GBIF occurrence dataset references as a
    citation file and email it to the user.
    """
    from django.contrib.auth import get_user_model
    from django.conf import settings
    from django.core.files.base import ContentFile
    from django.core.mail import EmailMultiAlternatives
    from django.template.loader import render_to_string
    from bims.models.source_reference import SourceReference
    from bims.models.download_request import DownloadRequest
    from bims.models.dataset import Dataset

    User = get_user_model()

    try:
        dr = DownloadRequest.objects.get(id=download_request_id)
    except DownloadRequest.DoesNotExist:
        logger.error('DownloadRequest %s not found', download_request_id)
        return 'DownloadRequest not found'

    def _fail(message: str) -> str:
        dr.processing = False
        dr.rejected = True
        dr.rejection_message = message
        dr.save(update_fields=['processing', 'rejected', 'rejection_message'])
        logger.error('Citation download %s failed: %s', download_request_id, message)
        return message

    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return _fail(f'User {user_id} not found')

    refs = list(SourceReference.objects.filter(id__in=source_reference_ids))
    datasets = list(Dataset.objects.filter(id__in=(dataset_ids or [])))
    total = len(refs) + len(datasets)

    if total == 0:
        return _fail('No matching source references found')

    try:
        separator = '\n'
        lines = []
        for i, ref in enumerate(refs, start=1):
            try:
                lines.append(_format_reference(ref, citation_format))
            except Exception as exc:
                logger.warning('Failed to format reference %s: %s', ref.id, exc)
            dr.progress = f'{i}/{total}'
            dr.save(update_fields=['progress'])

        for j, dataset in enumerate(datasets, start=len(refs) + 1):
            try:
                lines.append(_format_dataset(dataset, citation_format))
            except Exception as exc:
                logger.warning('Failed to format dataset %s: %s', dataset.id, exc)
            dr.progress = f'{j}/{total}'
            dr.save(update_fields=['progress'])

        content = separator.join(lines)
        ext = _file_extension(citation_format)
        file_name = f'citations_{datetime.today().strftime("%Y%m%d")}'

        # Attach the generated citation file to the DownloadRequest so it is
        # retrievable via the download-request file API endpoint.
        dr.request_file.save(
            f'{file_name}.{ext}',
            ContentFile(content.encode('utf-8')),
            save=False,
        )
        dr.request_category = f'{file_name}_{citation_format}'
        dr.processing = False
        dr.rejected = False
        dr.progress = f'{total}/{total}'
        dr.save(update_fields=[
            'request_file', 'request_category', 'processing', 'rejected', 'progress'
        ])
    except Exception as exc:
        return _fail(str(exc))

    zip_buf = io.BytesIO()
    with zipfile.ZipFile(zip_buf, 'w', zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(f'{file_name}.{ext}', content)
    zip_buf.seek(0)

    current_site = get_current_domain()
    ctx = {
        'username': user.get_full_name() or user.username,
        'current_site': current_site,
        'citation_format': citation_format,
        'total': total,
        'download_request_id': download_request_id,
    }
    subject = render_to_string(
        'citation_download/citation_created_subject.txt', ctx
    ).strip()
    message = render_to_string(
        'citation_download/citation_created_message.txt', ctx
    )

    msg = EmailMultiAlternatives(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
    )
    msg.attach(
        f'{file_name}.zip',
        zip_buf.getvalue(),
        'application/zip',
    )
    msg.content_subtype = 'html'
    msg.send()

    logger.info(
        'Citation download (%s, %s refs) sent to %s',
        citation_format, total, user.email,
    )
    return f'Sent {total} citations ({citation_format}) to {user.email}'
