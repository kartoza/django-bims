import requests
from datetime import date
from td_biblio.models.bibliography import Entry, Author, AuthorEntryRank
from td_biblio.utils.loaders import DOILoader, DOILoaderError
from geonode.documents.models import Document
from bims.utils.user import create_users_from_string
from bims.models import (
    DatabaseRecord,
    SourceReference,
    SourceReferenceBibliography,
    BimsDocument
)


def get_or_create_data_from_model(model, fields, create = True):
    """
    Get or create data from model.
    If multiple data returned then return the first one
    """
    try:
        if create:
            data, _ = model.objects.get_or_create(
                **fields
            )
        else:
            data = model.objects.get(
                **fields
            )
    except model.MultipleObjectsReturned:
        data = model.objects.filter(
            **fields
        )[0]
    except model.DoesNotExist:
        return None
    return data


def process_source_reference(
        reference = None,
        reference_category = None,
        doi = None,
        document_link = None,
        document_url = None,
        document_title = None,
        document_author = None,
        source_year = None):
    """Processing source reference data from csv"""
    source_reference = None
    document_id = 0
    document = None
    source_reference_found = False

    if (
        not reference and
        not reference_category and
        not doi and
        not document_link and
        not document_url and
        not document_title and
        not document_author and
        not source_year
    ):
        return '', None

    if not reference:
        if document_title:
            reference = document_title
    if not document_title and reference:
        document_title = reference

    # If the reference is published report or thesis, author is required
    if (reference_category.lower().startswith('published') or
            'thesis' in reference_category.lower()) and not document_author:
        return 'Missing author for published report or thesis', None

    # if there is document link, get the id of the document
    if document_link:
        try:
            doc_split = document_link.split('/')
            document_id = int(doc_split[len(doc_split) - 1])
            document = Document.objects.get(id=document_id)
        except (ValueError, Document.DoesNotExist):
            return 'Document {} does not exist'.format(document_id), None

    # if there is document url, get or create document based on url
    if document_url:
        document_fields = {
            'doc_url': document_url
        }
        if source_year:
            document_fields['date'] = date(
                year=int(source_year),
                month=1,
                day=1
            )
        authors = create_users_from_string(document_author)
        if len(authors) > 0:
            author = authors[0]
        else:
            author = None
        document_fields['owner'] = author
        document = get_or_create_data_from_model(
            Document,
            document_fields
        )
        try:
            bims_document, _ = BimsDocument.objects.get_or_create(
                document=document
            )
        except BimsDocument.MultipleObjectsReturned:
            bims_document = BimsDocument.objects.filter(
                document=document
            )[0]
        for author in authors:
            bims_document.authors.add(author)
        if document.title != document_title:
            document.title = document_title
            document.save()

    # if DOI provided, check in bibliography records
    if doi:
        entry = get_or_create_data_from_model(
            model=Entry,
            fields={
                'doi': doi
            },
            create=False
        )
        if not entry:
            doi_loader = DOILoader()
            try:
                doi_loader.load_records(DOIs=[doi])
                doi_loader.save_records()
                entry_fields = {
                    'doi__iexact': doi
                }
                entry = get_or_create_data_from_model(
                    Entry,
                    entry_fields,
                    create=False
                )
                if entry:
                    source_reference = (
                        SourceReference.create_source_reference(
                            category='bibliography',
                            source_id=entry.id,
                            note=None
                        )
                    )
                    source_reference_found = True
            except (
                    DOILoaderError,
                    requests.exceptions.HTTPError) as e:
                print(e)
            finally:
                if not entry:
                    return 'Error Fetching DOI : {doi}'.format(
                        doi=doi), None
                if entry and not source_reference:
                    SourceReference.create_source_reference(
                        category='bibliography',
                        source_id=entry.id,
                        note=None
                    )
                    source_reference, _ = (
                        SourceReferenceBibliography.objects.get_or_create(
                            source=entry
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
            if (
                    document_url is not None and
                    document_title and
                    document_author and
                    source_year
            ):
                optional_values = {}
                if doi:
                    optional_values['doi'] = doi
                entry, _ = Entry.objects.get_or_create(
                    url=document_url,
                    title=document_title,
                    publication_date=date(
                        int(source_year), 1, 1),
                    is_partial_publication_date=True,
                    type='article',
                    **optional_values
                )
                authors = create_users_from_string(document_author)
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
                return 'Peer reviewed should have a DOI', None
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
            if source_year:
                reference_name += ', ' + source_year
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
            if source_year:
                reference_name += ', ' + source_year
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
        source_reference.save()
    elif reference and not source_reference:
        return 'Reference {} is not created'.format(
                reference), None

    return 'Reference created', source_reference
