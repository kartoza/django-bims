import requests
from datetime import date
from scripts.management.csv_command import CsvCommand
from bims.utils.logger import log
from bims.models import (
    BiologicalCollectionRecord,
    DatabaseRecord,
    SourceReference,
    SourceReferenceBibliography
)
from td_biblio.models.bibliography import Entry, Author, AuthorEntryRank
from td_biblio.utils.loaders import DOILoader, DOILoaderError
from bims.utils.user import create_users_from_string
from geonode.documents.models import Document

NOTES = 'Notes'
REFERENCE = 'Reference'
REFERENCE_CATEGORY = 'Reference category'
DOI = 'DOI'
DOCUMENT_UPLOAD_LINK = 'Document Upload Link'
DOCUMENT_URL = 'URL'
DOCUMENT_TITLE = 'Title'
DOCUMENT_AUTHOR = 'Author(s)'
SOURCE_YEAR = 'Year'
SOURCE = 'Source'


class Command(CsvCommand):

    def source_reference(self, record, index):
        source_reference = None
        reference = record[SOURCE]
        reference_category = record[REFERENCE_CATEGORY]
        doi = record[DOI].strip()
        document_link = record[DOCUMENT_UPLOAD_LINK]
        document_url = record[DOCUMENT_URL]
        document_id = 0
        document = None
        source_reference_found = False

        # if there is document link, get the id of the document
        if document_link:
            try:
                doc_split = document_link.split('/')
                document_id = int(doc_split[len(doc_split) - 1])
                document = Document.objects.get(id=document_id)
            except (ValueError, Document.DoesNotExist):
                log('Document {} does not exist'.format(document_id))

        # if there is document url, get or create document based on url
        if document_url:
            document_fields = {
                'doc_url': document_url,
                'title': record[DOCUMENT_TITLE],
            }
            if record[SOURCE_YEAR]:
                document_fields['date'] = date(
                    year=int(record[SOURCE_YEAR]),
                    month=1,
                    day=1
                )
            authors = create_users_from_string(record[DOCUMENT_AUTHOR])
            if len(authors) > 0:
                author = authors[0]
            else:
                author = None
            document_fields['owner'] = author
            document, document_created = Document.objects.get_or_create(
                **document_fields
            )

        # if DOI provided, check in bibliography records
        if doi:
            try:
                try:
                    entry = Entry.objects.get(
                        doi=doi
                    )
                except Entry.MultipleObjectsReturned:
                    entry = Entry.objects.filter(doi=doi)[0]
                try:
                    source_reference = SourceReferenceBibliography.objects.get(
                        source=entry
                    )
                except SourceReferenceBibliography.DoesNotExist:
                    source_reference = (
                        SourceReferenceBibliography.objects.create(
                            source=entry
                        )
                    )
                source_reference_found = True
            except Entry.DoesNotExist:
                doi_loader = DOILoader()
                try:
                    doi_loader.load_records(DOIs=[doi])
                    doi_loader.save_records()
                    entry = Entry.objects.get(doi__iexact=doi)
                    source_reference = (
                        SourceReference.create_source_reference(
                            category='bibliography',
                            source_id=entry.id,
                            note=None
                        )
                    )
                    source_reference_found = True
                except (DOILoaderError, requests.exceptions.HTTPError, Entry.DoesNotExist):
                    log(
                        'Error Fetching DOI : {doi}'.format(
                            doi=doi,
                        ),
                        index
                    )
                except Entry.MultipleObjectsReturned:
                    entry = Entry.objects.filter(doi__iexact=doi)[0]
                    source_reference = (
                        SourceReference.create_source_reference(
                            category='bibliography',
                            source_id=entry.id,
                            note=None
                        )
                    )
                    source_reference_found = True

        if not source_reference_found:
            if (
                    'peer-reviewed' in reference_category.lower()
            ):
                # Peer reviewed
                # should be bibliography type
                # If url, title, year, and author(s) exists, crete new entry
                if record[DOCUMENT_URL] and record[DOCUMENT_TITLE] and record[DOCUMENT_AUTHOR] and record[SOURCE_YEAR]:
                    optional_values = {}
                    if doi:
                        optional_values['doi'] = doi
                    entry, _ = Entry.objects.get_or_create(
                        url=record[DOCUMENT_URL],
                        title=record[DOCUMENT_TITLE],
                        publication_date=date(int(record[SOURCE_YEAR]), 1, 1),
                        is_partial_publication_date=True,
                        type='article',
                        **optional_values
                    )
                    authors = create_users_from_string(record[DOCUMENT_AUTHOR])
                    rank = 1
                    for author in authors:
                        _author, _ = Author.objects.get_or_create(
                            first_name=author.first_name,
                            last_name=author.last_name,
                            user=author
                        )
                        AuthorEntryRank.objects.get_or_create(
                            author=_author,
                            entry=entry,
                            rank=rank
                        )
                        rank += 1
                    try:
                        source_reference = SourceReferenceBibliography.objects.get(
                            source=entry
                        )
                    except SourceReferenceBibliography.DoesNotExist:
                        source_reference = (
                            SourceReferenceBibliography.objects.create(
                                source=entry
                            )
                        )
                else:
                    raise ValueError('Peer reviewed should have a DOI')
            elif (
                    reference_category.lower().startswith('published') or
                    'thesis' in reference_category.lower()
            ):
                # Document
                if document:
                    source_reference = (
                        SourceReference.create_source_reference(
                            category='document',
                            source_id=document.id,
                            note=None
                        )
                    )
            elif 'database' in reference_category.lower():
                reference_name = reference
                if record[SOURCE_YEAR]:
                    reference_name += ', ' + record[SOURCE_YEAR]
                database_record, dr_created = (
                    DatabaseRecord.objects.get_or_create(
                        name=reference_name
                    )
                )
                source_reference = (
                    SourceReference.create_source_reference(
                        category='database',
                        source_id=database_record.id,
                        note=None
                    )
                )
            else:
                # Unpublished data
                reference_name = reference
                if record[SOURCE_YEAR]:
                    reference_name += ', ' + record[SOURCE_YEAR]
                source_reference = (
                    SourceReference.create_source_reference(
                        category=None,
                        source_id=None,
                        note=reference_name
                    )
                )
        if (
                document and
                source_reference and
                not isinstance(source_reference.source, Document)):
            source_reference.document = document
            source_reference.save()

        if reference and source_reference:
            source_reference.source_name = reference
        elif reference and not source_reference:
            log(
                'Reference {} is not created'.format(
                    reference
                ),
                index)

        return source_reference

    def csv_dict_reader(self, csv_reader):
        for row in csv_reader:
            print(row)
