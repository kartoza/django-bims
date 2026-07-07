# coding=utf-8
"""Tests for export_coldp_zip task - metadata.yaml generation."""

import io
import shutil
import tempfile
import yaml
import zipfile
import datetime
from unittest.mock import patch

from django.test import override_settings
from django_tenants.test.cases import FastTenantTestCase

from bims.models.checklist_version import ChecklistVersion, ChecklistSnapshot
from bims.models.download_request import DownloadRequest
from bims.models.licence import Licence
from bims.models.taxonomy_checklist import TaxonomyChecklist
from bims.tests.model_factories import (
    TaxonGroupF, UserF,
    SourceReferenceF, SourceReferenceBibliographyF,
    SourceReferenceDatabaseF, SourceReferenceDocumentF,
    DatabaseRecordF, DocumentF,
)
from bims.factories import (
    EntryFactory, AuthorEntryRankFactory, AuthorFactory,
)


def _licence():
    obj, _ = Licence.objects.get_or_create(
        identifier='CC-BY-4.0',
        defaults={
            'name': 'Creative Commons Attribution 4.0',
            'url': 'https://creativecommons.org/licenses/by/4.0/',
        },
    )
    return obj


class TestExportColdpZipMetadata(FastTenantTestCase):
    """Tests for the metadata.yaml content in the COLdP ZIP produced by export_coldp_zip."""

    def setUp(self):
        self.group = TaxonGroupF.create(name='Fish')
        self.user = UserF.create(
            first_name='Alice', last_name='Smith', email='alice@example.com'
        )
        self.licence = _licence()
        self._tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self._tmpdir, ignore_errors=True)

    # -----------------------------------------------------------------------
    # Helpers
    # -----------------------------------------------------------------------

    def _make_version(self, checklist=None, **kwargs):
        defaults = dict(
            taxon_group=self.group,
            version='1.0',
            license=self.licence,
            status=ChecklistVersion.STATUS_PUBLISHED,
        )
        defaults.update(kwargs)
        if checklist is not None:
            defaults['checklist'] = checklist
        return ChecklistVersion.objects.create(**defaults)

    def _make_dr(self):
        return DownloadRequest.objects.create(
            requester=self.user,
            approved=True,
            processing=True,
        )

    def _make_snapshot(self, version, reference_id='', **kwargs):
        uid = ChecklistSnapshot.objects.filter(checklist_version=version).count() + 1
        defaults = dict(
            checklist_version=version,
            checklist_id=f'test:{uid}',
            scientific_name='Testus testus',
            rank='SPECIES',
            reference_id=str(reference_id) if reference_id else '',
        )
        defaults.update(kwargs)
        return ChecklistSnapshot.objects.create(**defaults)

    def _run_task(self, version, dr):
        """Run export_coldp_zip and return parsed metadata.yaml dict."""
        from bims.tasks.coldp_export import export_coldp_zip
        with override_settings(MEDIA_ROOT=self._tmpdir):
            with patch('bims.tasks.email_csv.send_csv_via_email'):
                export_coldp_zip(dr.id, str(version.pk))
            dr.refresh_from_db()
            zip_path = dr.request_file.path
        with open(zip_path, 'rb') as f:
            zip_bytes = f.read()
        with zipfile.ZipFile(io.BytesIO(zip_bytes), 'r') as zf:
            return yaml.safe_load(zf.read('metadata.yaml'))

    # -----------------------------------------------------------------------
    # Basic scalar fields
    # -----------------------------------------------------------------------

    def test_title_fallback_to_module_name(self):
        version = self._make_version()
        dr = self._make_dr()
        metadata = self._run_task(version, dr)
        self.assertEqual(metadata['title'], 'Fish Checklist')

    def test_title_from_checklist(self):
        checklist = TaxonomyChecklist.objects.create(
            title='My Freshwater Fish Checklist', version='1.0'
        )
        version = self._make_version(checklist=checklist)
        dr = self._make_dr()
        metadata = self._run_task(version, dr)
        self.assertEqual(metadata['title'], 'My Freshwater Fish Checklist')

    def test_version_field(self):
        version = self._make_version(version='3.1')
        dr = self._make_dr()
        metadata = self._run_task(version, dr)
        self.assertEqual(metadata['version'], '3.1')

    def test_alias_is_taxon_group_name(self):
        version = self._make_version()
        dr = self._make_dr()
        metadata = self._run_task(version, dr)
        self.assertEqual(metadata['alias'], 'Fish')

    def test_taxonomic_scope_is_taxon_group_name(self):
        version = self._make_version()
        dr = self._make_dr()
        metadata = self._run_task(version, dr)
        self.assertEqual(metadata['taxonomicScope'], 'Fish')

    def test_license_field(self):
        version = self._make_version()
        dr = self._make_dr()
        metadata = self._run_task(version, dr)
        self.assertEqual(metadata['license'], 'CC-BY-4.0')

    def test_doi_field(self):
        version = self._make_version(doi='10.1234/test')
        dr = self._make_dr()
        metadata = self._run_task(version, dr)
        self.assertEqual(metadata['doi'], '10.1234/test')

    def test_doi_absent_when_not_set(self):
        version = self._make_version(doi='')
        dr = self._make_dr()
        metadata = self._run_task(version, dr)
        self.assertNotIn('doi', metadata)

    def test_doi_in_identifier_list(self):
        version = self._make_version(doi='10.1234/test')
        dr = self._make_dr()
        metadata = self._run_task(version, dr)
        self.assertIn('10.1234/test', metadata['identifier'])

    def test_dataset_key_in_identifier_list(self):
        version = self._make_version(dataset_key='12345')
        dr = self._make_dr()
        metadata = self._run_task(version, dr)
        self.assertIn('col:12345', metadata['identifier'])

    def test_identifier_absent_when_no_doi_or_key(self):
        version = self._make_version(doi='', dataset_key='')
        dr = self._make_dr()
        metadata = self._run_task(version, dr)
        self.assertNotIn('identifier', metadata)

    # -----------------------------------------------------------------------
    # issued date
    # -----------------------------------------------------------------------

    def test_issued_from_checklist_released_at(self):
        checklist = TaxonomyChecklist.objects.create(
            title='Test', version='1.0',
            released_at=datetime.date(2024, 6, 15),
        )
        version = self._make_version(checklist=checklist)
        dr = self._make_dr()
        metadata = self._run_task(version, dr)
        self.assertEqual(metadata['issued'], '2024-06-15')

    def test_issued_from_published_at_when_no_checklist(self):
        from django.utils import timezone
        version = self._make_version()
        version.published_at = timezone.datetime(2025, 3, 10, tzinfo=datetime.timezone.utc)
        version.save(update_fields=['published_at'])
        dr = self._make_dr()
        metadata = self._run_task(version, dr)
        self.assertEqual(metadata['issued'], '2025-03-10')

    def test_issued_falls_back_to_today(self):
        version = self._make_version()
        version.published_at = None
        version.save(update_fields=['published_at'])
        dr = self._make_dr()
        metadata = self._run_task(version, dr)
        self.assertEqual(metadata['issued'], datetime.date.today().isoformat())

    # -----------------------------------------------------------------------
    # description
    # -----------------------------------------------------------------------

    def test_description_from_checklist(self):
        checklist = TaxonomyChecklist.objects.create(
            title='Test', version='1.0', description='Checklist abstract.'
        )
        version = self._make_version(checklist=checklist)
        dr = self._make_dr()
        metadata = self._run_task(version, dr)
        self.assertEqual(metadata['description'], 'Checklist abstract.')

    def test_description_fallback_to_version_notes(self):
        version = self._make_version(notes='Version release notes.')
        dr = self._make_dr()
        metadata = self._run_task(version, dr)
        self.assertEqual(metadata['description'], 'Version release notes.')

    def test_description_absent_when_empty(self):
        version = self._make_version(notes='')
        dr = self._make_dr()
        metadata = self._run_task(version, dr)
        self.assertNotIn('description', metadata)

    # -----------------------------------------------------------------------
    # contact / creator
    # -----------------------------------------------------------------------

    def test_contact_from_checklist(self):
        contact = UserF.create(
            first_name='Bob', last_name='Jones', email='bob@example.com'
        )
        checklist = TaxonomyChecklist.objects.create(
            title='Test', version='1.0', contact=contact
        )
        version = self._make_version(checklist=checklist)
        dr = self._make_dr()
        metadata = self._run_task(version, dr)
        self.assertEqual(metadata['contact']['given'], 'Bob')
        self.assertEqual(metadata['contact']['family'], 'Jones')
        self.assertEqual(metadata['contact']['email'], 'bob@example.com')

    def test_contact_absent_when_no_checklist_contact(self):
        version = self._make_version()
        dr = self._make_dr()
        metadata = self._run_task(version, dr)
        self.assertNotIn('contact', metadata)

    def test_creator_from_checklist(self):
        u1 = UserF.create(first_name='Carol', last_name='Lee', email='carol@example.com')
        u2 = UserF.create(first_name='Dan', last_name='Park', email='dan@example.com')
        checklist = TaxonomyChecklist.objects.create(title='Test', version='1.0')
        checklist.creators.set([u1, u2])
        version = self._make_version(checklist=checklist)
        dr = self._make_dr()
        metadata = self._run_task(version, dr)
        names = {(c['given'], c['family']) for c in metadata['creator']}
        self.assertIn(('Carol', 'Lee'), names)
        self.assertIn(('Dan', 'Park'), names)

    def test_creator_absent_when_no_checklist(self):
        version = self._make_version()
        dr = self._make_dr()
        metadata = self._run_task(version, dr)
        self.assertNotIn('creator', metadata)

    # -----------------------------------------------------------------------
    # source — absent when no references
    # -----------------------------------------------------------------------

    def test_source_absent_when_no_references(self):
        version = self._make_version()
        self._make_snapshot(version, reference_id='')
        dr = self._make_dr()
        metadata = self._run_task(version, dr)
        self.assertNotIn('source', metadata)

    def test_source_absent_when_snapshot_table_is_empty(self):
        version = self._make_version()
        dr = self._make_dr()
        metadata = self._run_task(version, dr)
        self.assertNotIn('source', metadata)

    # -----------------------------------------------------------------------
    # source — bibliography (journal article)
    # -----------------------------------------------------------------------

    def test_source_from_bibliography_type_mapping(self):
        from td_biblio.models.bibliography import Entry
        entry = EntryFactory(
            type=Entry.ARTICLE, title='River Fish Survey',
            doi='10.9999/rfs', url='', volume='12', number='3',
            pages='100--110',
        )
        bib = SourceReferenceBibliographyF(source=entry)
        version = self._make_version()
        self._make_snapshot(version, reference_id=bib.pk)
        dr = self._make_dr()
        metadata = self._run_task(version, dr)
        source = metadata['source'][0]
        self.assertEqual(source['id'], str(bib.pk))
        self.assertEqual(source['type'], 'article-journal')
        self.assertEqual(source['title'], 'River Fish Survey')
        self.assertEqual(source['doi'], '10.9999/rfs')
        self.assertEqual(source['volume'], '12')
        self.assertEqual(source['issue'], '3')
        self.assertEqual(source['page'], '100--110')

    def test_source_bibliography_journal_as_container_title(self):
        from bims.factories import JournalFactory
        journal = JournalFactory(name='Freshwater Biology')
        entry = EntryFactory(journal=journal, title='A study')
        bib = SourceReferenceBibliographyF(source=entry)
        version = self._make_version()
        self._make_snapshot(version, reference_id=bib.pk)
        dr = self._make_dr()
        metadata = self._run_task(version, dr)
        self.assertEqual(metadata['source'][0]['containerTitle'], 'Freshwater Biology')

    def test_source_bibliography_authors(self):
        entry = EntryFactory(title='With Authors')
        AuthorEntryRankFactory(
            entry=entry,
            author=AuthorFactory(first_name='Jane', last_name='Doe'),
            rank=1,
        )
        AuthorEntryRankFactory(
            entry=entry,
            author=AuthorFactory(first_name='John', last_name='Smith'),
            rank=2,
        )
        bib = SourceReferenceBibliographyF(source=entry)
        version = self._make_version()
        self._make_snapshot(version, reference_id=bib.pk)
        dr = self._make_dr()
        metadata = self._run_task(version, dr)
        authors = metadata['source'][0]['author']
        self.assertEqual(len(authors), 2)
        family_names = {a['family'] for a in authors}
        self.assertIn('Doe', family_names)
        self.assertIn('Smith', family_names)

    def test_source_bibliography_partial_date_uses_year_only(self):
        from td_biblio.models.bibliography import Entry
        entry = EntryFactory(
            title='Year-only Date',
            publication_date=datetime.date(2019, 6, 1),
            is_partial_publication_date=True,
        )
        bib = SourceReferenceBibliographyF(source=entry)
        version = self._make_version()
        self._make_snapshot(version, reference_id=bib.pk)
        dr = self._make_dr()
        metadata = self._run_task(version, dr)
        self.assertEqual(metadata['source'][0]['issued'], '2019')

    def test_source_bibliography_full_date_uses_iso(self):
        entry = EntryFactory(
            title='Full Date',
            publication_date=datetime.date(2020, 11, 30),
            is_partial_publication_date=False,
        )
        bib = SourceReferenceBibliographyF(source=entry)
        version = self._make_version()
        self._make_snapshot(version, reference_id=bib.pk)
        dr = self._make_dr()
        metadata = self._run_task(version, dr)
        self.assertEqual(metadata['source'][0]['issued'], '2020-11-30')

    def test_source_bibliography_book_type(self):
        from td_biblio.models.bibliography import Entry
        entry = EntryFactory(type=Entry.BOOK, title='A Book')
        bib = SourceReferenceBibliographyF(source=entry)
        version = self._make_version()
        self._make_snapshot(version, reference_id=bib.pk)
        dr = self._make_dr()
        metadata = self._run_task(version, dr)
        self.assertEqual(metadata['source'][0]['type'], 'book')

    def test_source_bibliography_publisher_and_address(self):
        from bims.factories import PublisherFactory
        pub = PublisherFactory(name='Oxford University Press')
        entry = EntryFactory(title='Published Work', publisher=pub, address='Oxford, UK')
        bib = SourceReferenceBibliographyF(source=entry)
        version = self._make_version()
        self._make_snapshot(version, reference_id=bib.pk)
        dr = self._make_dr()
        metadata = self._run_task(version, dr)
        src = metadata['source'][0]
        self.assertEqual(src['publisher'], 'Oxford University Press')
        self.assertEqual(src['publisherPlace'], 'Oxford, UK')

    def test_source_bibliography_isbn_issn(self):
        entry = EntryFactory(title='ISBN/ISSN Work', isbn='978-0-19-880673-3', issn='1234-5678')
        bib = SourceReferenceBibliographyF(source=entry)
        version = self._make_version()
        self._make_snapshot(version, reference_id=bib.pk)
        dr = self._make_dr()
        metadata = self._run_task(version, dr)
        src = metadata['source'][0]
        self.assertEqual(src['isbn'], '978-0-19-880673-3')
        self.assertEqual(src['issn'], '1234-5678')

    # -----------------------------------------------------------------------
    # source — database
    # -----------------------------------------------------------------------

    def test_source_from_database(self):
        db_record = DatabaseRecordF(
            name='FreshwaterDB', url='https://freshwater.example.com',
            description='Freshwater biodiversity records.'
        )
        db_ref = SourceReferenceDatabaseF(source=db_record)
        version = self._make_version()
        self._make_snapshot(version, reference_id=db_ref.pk)
        dr = self._make_dr()
        metadata = self._run_task(version, dr)
        src = metadata['source'][0]
        self.assertEqual(src['id'], str(db_ref.pk))
        self.assertEqual(src['type'], 'dataset')
        self.assertEqual(src['title'], 'FreshwaterDB')
        self.assertEqual(src['url'], 'https://freshwater.example.com')
        self.assertEqual(src['note'], 'Freshwater biodiversity records.')

    def test_source_database_issued_from_source_date(self):
        db_record = DatabaseRecordF(name='TimedDB')
        db_ref = SourceReferenceDatabaseF(
            source=db_record,
            source_date=datetime.date(2022, 4, 1),
        )
        version = self._make_version()
        self._make_snapshot(version, reference_id=db_ref.pk)
        dr = self._make_dr()
        metadata = self._run_task(version, dr)
        self.assertEqual(metadata['source'][0]['issued'], '2022-04-01')

    # -----------------------------------------------------------------------
    # source — document / report
    # -----------------------------------------------------------------------

    def test_source_from_document(self):
        doc = DocumentF(title='Field Survey Report 2023')
        doc_ref = SourceReferenceDocumentF(source=doc)
        version = self._make_version()
        self._make_snapshot(version, reference_id=doc_ref.pk)
        dr = self._make_dr()
        metadata = self._run_task(version, dr)
        src = metadata['source'][0]
        self.assertEqual(src['id'], str(doc_ref.pk))
        self.assertEqual(src['type'], 'report')
        self.assertEqual(src['title'], 'Field Survey Report 2023')

    def test_source_document_issued_from_source_date(self):
        doc = DocumentF(title='Report')
        doc_ref = SourceReferenceDocumentF(
            source=doc,
            source_date=datetime.date(2021, 9, 15),
        )
        version = self._make_version()
        self._make_snapshot(version, reference_id=doc_ref.pk)
        dr = self._make_dr()
        metadata = self._run_task(version, dr)
        self.assertEqual(metadata['source'][0]['issued'], '2021-09-15')

    # -----------------------------------------------------------------------
    # source — unpublished (base SourceReference)
    # -----------------------------------------------------------------------

    def test_source_from_unpublished_reference(self):
        ref = SourceReferenceF(
            source_name='Unpublished survey data',
            note='Collected in the field',
            source_date=datetime.date(2023, 1, 1),
        )
        version = self._make_version()
        self._make_snapshot(version, reference_id=ref.pk)
        dr = self._make_dr()
        metadata = self._run_task(version, dr)
        src = metadata['source'][0]
        self.assertEqual(src['id'], str(ref.pk))
        self.assertEqual(src['type'], 'manuscript')
        self.assertEqual(src['note'], 'Collected in the field')
        self.assertEqual(src['issued'], '2023-01-01')

    # -----------------------------------------------------------------------
    # source — ID linkage and deduplication
    # -----------------------------------------------------------------------

    def test_source_id_matches_snapshot_reference_id(self):
        entry = EntryFactory(title='Linked Reference')
        bib = SourceReferenceBibliographyF(source=entry)
        version = self._make_version()
        self._make_snapshot(version, reference_id=bib.pk)
        dr = self._make_dr()
        metadata = self._run_task(version, dr)
        self.assertEqual(metadata['source'][0]['id'], str(bib.pk))

    def test_source_deduplicates_shared_reference(self):
        entry = EntryFactory(title='Shared Reference')
        bib = SourceReferenceBibliographyF(source=entry)
        version = self._make_version()
        # Two snapshots pointing at the same reference
        self._make_snapshot(version, reference_id=bib.pk)
        self._make_snapshot(version, reference_id=bib.pk, checklist_id='test:dup')
        dr = self._make_dr()
        metadata = self._run_task(version, dr)
        source_ids = [s['id'] for s in metadata['source']]
        self.assertEqual(len(source_ids), len(set(source_ids)))

    def test_source_excludes_refs_not_in_snapshot(self):
        entry_used = EntryFactory(title='Used Reference')
        entry_unused = EntryFactory(title='Unused Reference')
        bib_used = SourceReferenceBibliographyF(source=entry_used)
        SourceReferenceBibliographyF(source=entry_unused)
        version = self._make_version()
        self._make_snapshot(version, reference_id=bib_used.pk)
        dr = self._make_dr()
        metadata = self._run_task(version, dr)
        source_ids = {s['id'] for s in metadata['source']}
        self.assertIn(str(bib_used.pk), source_ids)
        self.assertEqual(len(source_ids), 1)

    def test_source_multiple_distinct_references(self):
        entry1 = EntryFactory(title='Reference A')
        entry2 = EntryFactory(title='Reference B')
        bib1 = SourceReferenceBibliographyF(source=entry1)
        bib2 = SourceReferenceBibliographyF(source=entry2)
        version = self._make_version()
        self._make_snapshot(version, reference_id=bib1.pk)
        self._make_snapshot(version, reference_id=bib2.pk, checklist_id='test:2')
        dr = self._make_dr()
        metadata = self._run_task(version, dr)
        self.assertEqual(len(metadata['source']), 2)
        titles = {s['title'] for s in metadata['source']}
        self.assertIn('Reference A', titles)
        self.assertIn('Reference B', titles)
