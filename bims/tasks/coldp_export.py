# coding=utf-8
"""Celery task: export a published ChecklistVersion as a ColDP ZIP."""
import csv
import io
import logging
import zipfile
from datetime import date

import yaml
from celery import shared_task
from django.core.files.base import ContentFile

logger = logging.getLogger(__name__)


def build_coldp_source_entries(name_usage_rows):
    """Build COLdP source entries for distinct SourceReferences in snapshot rows."""
    ref_ids = {row['referenceID'] for row in name_usage_rows if row.get('referenceID')}
    if not ref_ids:
        return []

    int_ids = set()
    for rid in ref_ids:
        try:
            int_ids.add(int(rid))
        except (ValueError, TypeError):
            pass

    if not int_ids:
        return []

    from bims.models.source_reference import (
        SourceReference,
        SourceReferenceBibliography,
        SourceReferenceDatabase,
        SourceReferenceDocument,
    )

    BIBTEX_TO_CSL = {
        'article':       'article-journal',
        'book':          'book',
        'booklet':       'book',
        'conference':    'paper-conference',
        'inbook':        'chapter',
        'incollection':  'chapter',
        'inproceedings': 'paper-conference',
        'manual':        'document',
        'mastersthesis': 'thesis',
        'misc':          'document',
        'phdthesis':     'thesis',
        'proceedings':   'book',
        'techreport':    'report',
        'unpublished':   'manuscript',
    }

    def _csl_names(author_objects):
        result = []
        for a in author_objects:
            agent = {}
            if getattr(a, 'first_name', ''):
                agent['given'] = a.first_name
            if getattr(a, 'last_name', ''):
                agent['family'] = a.last_name
            if agent:
                result.append(agent)
        return result or None

    def _child_reference(ref, attr):
        try:
            return getattr(ref, attr)
        except (
            SourceReferenceBibliography.DoesNotExist,
            SourceReferenceDatabase.DoesNotExist,
            SourceReferenceDocument.DoesNotExist,
        ):
            return None

    refs = (
        SourceReference.objects
        .non_polymorphic()
        .filter(id__in=int_ids)
        .select_related(
            'sourcereferencebibliography__source__journal',
            'sourcereferencebibliography__source__publisher',
            'sourcereferencedatabase__source',
            'sourcereferencedocument__source',
        )
    )

    source_entries = []
    for ref in refs:
        entry = {'id': str(ref.pk)}

        bib = _child_reference(ref, 'sourcereferencebibliography')
        db = _child_reference(ref, 'sourcereferencedatabase')
        doc = _child_reference(ref, 'sourcereferencedocument')

        if bib and bib.source:
            src = bib.source
            entry['type'] = BIBTEX_TO_CSL.get(src.type, 'document')
            entry['title'] = src.title
            if src.doi:
                entry['doi'] = src.doi
            if src.url:
                entry['url'] = src.url
            authors = _csl_names(src.get_authors())
            if authors:
                entry['author'] = authors
            editors = _csl_names(list(src.editors.all()))
            if editors:
                entry['editor'] = editors
            if src.publication_date:
                entry['issued'] = (
                    str(src.publication_date.year)
                    if src.is_partial_publication_date
                    else src.publication_date.isoformat()
                )
            if src.journal:
                entry['containerTitle'] = src.journal.name
            if src.booktitle:
                entry['containerTitle'] = src.booktitle
            if src.volume:
                entry['volume'] = src.volume
            if src.number:
                entry['issue'] = src.number
            if src.pages:
                entry['page'] = src.pages
            if src.edition:
                entry['edition'] = src.edition
            if src.publisher:
                entry['publisher'] = src.publisher.name
            if src.address:
                entry['publisherPlace'] = src.address
            if src.isbn:
                entry['isbn'] = src.isbn
            if src.issn:
                entry['issn'] = src.issn
            if src.note:
                entry['note'] = src.note

        elif db and db.source:
            entry['type'] = 'dataset'
            entry['title'] = db.source.name
            if db.source.url:
                entry['url'] = db.source.url
            if db.source.description:
                entry['note'] = db.source.description
            if ref.source_date:
                entry['issued'] = ref.source_date.isoformat()

        elif doc and doc.source:
            entry['type'] = 'report'
            entry['title'] = doc.source.title
            if ref.source_date:
                entry['issued'] = ref.source_date.isoformat()
            authors = _csl_names(ref.author_list)
            if authors:
                entry['author'] = authors

        else:
            entry['type'] = 'manuscript'
            entry['title'] = ref.title or ref.source_name or ''
            if ref.source_date:
                entry['issued'] = ref.source_date.isoformat()
            if ref.note:
                entry['note'] = ref.note

        if entry.get('title'):
            source_entries.append(entry)

    return source_entries


@shared_task(name='bims.tasks.export_coldp_zip', queue='update', ignore_result=True)
def export_coldp_zip(download_request_id, checklist_version_id):
    from django.utils import timezone

    from bims.models.checklist_version import ChecklistSnapshot, ChecklistVersion, ChecklistVersionContributor
    from bims.models.download_request import DownloadRequest
    from bims.tasks.email_csv import send_csv_via_email

    try:
        dr = DownloadRequest.objects.get(id=download_request_id)
    except DownloadRequest.DoesNotExist:
        logger.error('export_coldp_zip: DownloadRequest %s not found', download_request_id)
        return

    try:
        version = (
            ChecklistVersion.objects
            .select_related('taxon_group', 'license', 'checklist', 'checklist__contact', 'published_by')
            .prefetch_related('checklist__creators')
            .get(pk=checklist_version_id)
        )
    except ChecklistVersion.DoesNotExist:
        logger.error('export_coldp_zip: ChecklistVersion %s not found', checklist_version_id)
        dr.processing = False
        dr.save(update_fields=['processing'])
        return

    qs = (
        ChecklistSnapshot.objects
        .filter(checklist_version=version)
        .order_by('scientific_name', 'checklist_id')
    )
    total = qs.count()

    NAME_USAGE_COLS = [
        'taxonID', 'parentID', 'basionymID', 'rank', 'scientificName',
        'authorship', 'status', 'nameStatus', 'kingdom', 'phylum',
        'class', 'order', 'family', 'genus', 'remarks', 'referenceID',
    ]
    VERNACULAR_COLS = ['taxonID', 'name', 'language']
    DISTRIBUTION_COLS = ['taxonID', 'area', 'status']

    name_usage_rows = []
    vernacular_rows = []
    distribution_rows = []
    processed = 0

    for row in qs.iterator(chunk_size=500):
        name_usage_rows.append({
            'taxonID':        row.checklist_id,
            'parentID':       row.parent_checklist_id,
            'basionymID':     row.basionym_checklist_id,
            'rank':           row.rank,
            'scientificName': row.scientific_name,
            'authorship':     row.authorship,
            'status':         row.taxonomic_status,
            'nameStatus':     row.name_status,
            'kingdom':        row.kingdom,
            'phylum':         row.phylum,
            'class':          row.klass,
            'order':          row.order,
            'family':         row.family,
            'genus':          row.genus,
            'remarks':        row.remarks,
            'referenceID':    row.reference_id,
        })
        for vn in (row.vernacular_names or []):
            vernacular_rows.append({
                'taxonID':  row.checklist_id,
                'name':     vn.get('name', ''),
                'language': vn.get('language', ''),
            })
        for dist in (row.distributions or []):
            distribution_rows.append({
                'taxonID': row.checklist_id,
                'area':    dist.get('area', ''),
                'status':  dist.get('status', ''),
            })

        processed += 1
        if processed % 200 == 0:
            dr.progress = f'{processed}/{total}'
            dr.progress_updated_at = timezone.now()
            dr.save(update_fields=['progress', 'progress_updated_at'])

    def _write_tsv(cols, rows):
        buf = io.StringIO()
        writer = csv.DictWriter(
            buf, fieldnames=cols, delimiter='\t', extrasaction='ignore'
        )
        writer.writeheader()
        writer.writerows(rows)
        return buf.getvalue().encode('utf-8')

    # Build metadata.yaml following the COLdP metadata.yaml spec
    module_name = version.taxon_group.name if version.taxon_group_id is not None else ''
    checklist = version.checklist

    issued = (
        checklist.released_at.isoformat() if (checklist and checklist.released_at)
        else version.published_at.date().isoformat() if version.published_at
        else date.today().isoformat()
    )

    doi = version.doi or (checklist.doi if checklist else '') or ''
    title = (checklist.title if checklist and checklist.title else f'{module_name} Checklist')
    description = (
        (checklist.description if checklist and checklist.description else '') or version.notes
    )
    license_str = version.license.identifier if version.license_id else ''

    metadata = {}

    if doi:
        metadata['doi'] = doi

    identifiers = []
    if doi:
        identifiers.append(doi)
    if version.dataset_key:
        identifiers.append(f'col:{version.dataset_key}')
    if identifiers:
        metadata['identifier'] = identifiers

    metadata['title'] = title
    if module_name:
        metadata['alias'] = module_name
    if description:
        metadata['description'] = description

    metadata['issued'] = issued
    metadata['version'] = version.version

    if license_str:
        metadata['license'] = license_str

    def _agent(user):
        if not user:
            return None
        agent = {}
        if user.first_name:
            agent['given'] = user.first_name
        if user.last_name:
            agent['family'] = user.last_name
        if user.email:
            agent['email'] = user.email
        return agent or None

    if checklist and checklist.contact_id:
        contact_agent = _agent(checklist.contact)
        if contact_agent:
            metadata['contact'] = contact_agent

    if checklist:
        creators = list(checklist.creators.all())
        creator_agents = [a for a in (_agent(u) for u in creators) if a]
        if creator_agents:
            metadata['creator'] = creator_agents

    if module_name:
        metadata['taxonomicScope'] = module_name

    source_entries = build_coldp_source_entries(name_usage_rows)
    if source_entries:
        metadata['source'] = source_entries

    contrib_qs = (
        ChecklistVersionContributor.objects
        .filter(checklist_version=version)
        .select_related('user')
        .order_by('order', 'id')
    )
    contributor_agents = []
    for cv in contrib_qs:
        agent = {}
        if cv.user:
            if cv.user.first_name:
                agent['given'] = cv.user.first_name
            if cv.user.last_name:
                agent['family'] = cv.user.last_name
            if cv.user.email:
                agent['email'] = cv.user.email
        if cv.organisation:
            agent['organisation'] = cv.organisation
        if cv.note:
            agent['note'] = cv.note
        if agent:
            contributor_agents.append(agent)
    if contributor_agents:
        metadata['contributor'] = contributor_agents

    metadata_yaml = yaml.dump(
        metadata,
        default_flow_style=False,
        allow_unicode=True,
        sort_keys=False,
    )

    # Assemble ZIP in memory
    zip_buf = io.BytesIO()
    with zipfile.ZipFile(zip_buf, 'w', zipfile.ZIP_DEFLATED) as zf:
        zf.writestr('NameUsage.tsv',     _write_tsv(NAME_USAGE_COLS,   name_usage_rows))
        zf.writestr('VernacularName.tsv', _write_tsv(VERNACULAR_COLS,   vernacular_rows))
        zf.writestr('Distribution.tsv',  _write_tsv(DISTRIBUTION_COLS, distribution_rows))
        zf.writestr('metadata.yaml',     metadata_yaml.encode('utf-8'))

    # Persist to disk
    safe_module = module_name.replace(' ', '_')
    safe_version = version.version.replace(' ', '_').replace('/', '-')
    zip_filename = f'coldp_{safe_module}_{safe_version}.zip'
    dr.request_file.save(
        zip_filename,
        ContentFile(zip_buf.getvalue()),
        save=False,
    )
    dr.request_category = f'{module_name} {version.version}'
    dr.progress = f'{total}/{total}'
    dr.progress_updated_at = timezone.now()
    dr.processing = False
    dr.save(update_fields=[
        'request_file',
        'request_category',
        'progress',
        'progress_updated_at',
        'processing',
    ])
    if dr.requester_id and dr.request_file:
        send_csv_via_email.delay(
            user_id=dr.requester_id,
            csv_file=dr.request_file.path,
            file_name=dr.request_category or zip_filename,
            approved=dr.approved,
            download_request_id=dr.id,
        )
    logger.info('export_coldp_zip: wrote %s (%d rows)', zip_filename, total)
