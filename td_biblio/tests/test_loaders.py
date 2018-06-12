# -*- coding: utf-8 -*-
"""
TailorDev Bibliography

Test loaders.
"""
from __future__ import unicode_literals

import datetime
import pytest

from django.test import TestCase
from eutils.exceptions import EutilsNCBIError
from requests.exceptions import HTTPError

from ..exceptions import DOILoaderError, PMIDLoaderError
from ..utils.loaders import BibTeXLoader, DOILoader, PubmedLoader
from ..models import Author, Entry, Journal
from .fixtures.entries import PMIDs as FPMIDS, DOIs as FDOIS

FileNotFoundError = getattr(__builtins__, 'FileNotFoundError', IOError)


@pytest.mark.django_db
@pytest.mark.usefixtures('bibtex')
class BibTexLoaderTests(TestCase):
    """
    Tests for the BibTex loader
    """
    def setUp(self):
        """
        Set object level vars
        """
        self.loader = BibTeXLoader()

    def _save_records(self):
        self.loader.load_records(bibtex_filename=self.bibtex)
        self.loader.save_records()

    def test_load_records_from_a_bibtex_file(self):
        """Test records loading from an existing bibtex file"""
        self.loader.load_records(bibtex_filename=self.bibtex)

        self.assertEqual(len(self.loader.records), 9)

    def test_load_records_with_a_wrong_path(self):
        """Test records loading from a wrong bibtex file path"""
        with self.assertRaises(FileNotFoundError):
            self.loader.load_records(bibtex_filename='fake/path')

        self.assertEqual(len(self.loader.records), 0)

    def test_save_records_from_a_bibtex_file(self):
        """Test records saving from an existing bibtex file"""
        self.assertEqual(Entry.objects.count(), 0)

        self._save_records()

        self.assertEqual(Entry.objects.count(), 9)
        self.assertEqual(Journal.objects.count(), 5)
        self.assertEqual(Author.objects.count(), 31)

    def _test_entry_authors(self, entry, expected_authors):
        for rank, author in enumerate(entry.get_authors()):
            self.assertEqual(
                author.get_formatted_name(),
                expected_authors[rank]
            )

    def test_author_rank(self):
        """
        Test if author rank is respected
        """
        self._save_records()

        # Case 1
        entry = Entry.objects.get(
            title='Mobyle: a new full web bioinformatics framework'
        )
        expected_authors = [
            'Néron B',
            'Ménager H',
            'Maufrais C',
            'Joly N',
            'Maupetit J',
            'Letort S',
            'Carrere S',
            'Tuffery P',
            'Letondal C',
        ]
        self._test_entry_authors(entry, expected_authors)

        # Case 2
        entry = Entry.objects.get(title__startswith='fpocket')
        expected_authors = [
            'Schmidtke P',
            'Le Guilloux V',
            'Maupetit J',
            'Tufféry P'
        ]
        self._test_entry_authors(entry, expected_authors)

    def test_partial_publication_date(self):
        """Test if partial publication date flag"""
        self._save_records()

        qs = Entry.objects.filter(is_partial_publication_date=False)
        self.assertEqual(qs.count(), 1)

        qs = Entry.objects.filter(is_partial_publication_date=True)
        self.assertEqual(qs.count(), 8)


@pytest.mark.django_db
class PubmedLoaderTests(TestCase):
    """
    Tests for the pubmed loader
    """
    def setUp(self):
        """
        Set object level vars
        """
        self.PMID = 26588162
        self.loader = PubmedLoader()

    def test_load_records_given_an_existing_pmid(self):
        """Test single import given an existing PMID"""

        self.loader.load_records(PMIDs=self.PMID)

        self.assertEqual(len(self.loader.records), 1)

        record = self.loader.records[0]
        expected = {
            'title': (
                'Improved PEP-FOLD Approach for Peptide and Miniprotein '
                'Structure Prediction.'
            ),
            'authors': [
                {
                    'first_name': 'Y',
                    'last_name': 'Shen'
                },
                {
                    'first_name': 'J',
                    'last_name': 'Maupetit'
                },
                {
                    'first_name': 'P',
                    'last_name': 'Derreumaux'
                },
                {
                    'first_name': 'P',
                    'last_name': 'Tufféry'
                }
            ],
            'journal': 'J Chem Theory Comput',
            'volume': '10',
            'number': '10',
            'pages': '4745-58',
            'year': '2014',
            'publication_date': datetime.date(2014, 1, 1),
            'is_partial_publication_date': True
        }
        self.assertEqual(record['title'], expected['title'])
        self.assertEqual(record['authors'], expected['authors'])
        self.assertEqual(record['journal'], expected['journal'])
        self.assertEqual(record['volume'], expected['volume'])
        self.assertEqual(record['number'], expected['number'])
        self.assertEqual(record['pages'], expected['pages'])
        self.assertEqual(record['year'], expected['year'])
        self.assertEqual(
            record['publication_date'],
            expected['publication_date']
        )
        self.assertEqual(
            record['is_partial_publication_date'],
            expected['is_partial_publication_date']
        )

    def test_load_records_given_a_fake_string_as_pmid(self):
        """Test single import given a fake PMID"""

        with pytest.raises(EutilsNCBIError):
            self.loader.load_records(PMIDs='fakePMID')
        self.assertEqual(len(self.loader.records), 0)

    def test_save_records_from_an_existing_pmid(self):
        """Test single import given an existing PMID"""

        self.assertEqual(Author.objects.count(), 0)
        self.assertEqual(Entry.objects.count(), 0)
        self.assertEqual(Journal.objects.count(), 0)

        self.loader.load_records(PMIDs=self.PMID)
        self.loader.save_records()

        self.assertEqual(Author.objects.count(), 4)
        self.assertEqual(Entry.objects.count(), 1)
        self.assertEqual(Journal.objects.count(), 1)

    def test_save_records_from_mutiple_pmid(self):
        """Test batch import from multiple PMIDs"""

        self.assertEqual(Entry.objects.count(), 0)

        self.loader.load_records(PMIDs=FPMIDS)
        self.loader.save_records()

        self.assertEqual(Entry.objects.count(), len(FPMIDS))


@pytest.mark.django_db
class PubmedLoaderToRecordTests(TestCase):
    """
    Tests for the patched pubmed loader
    """
    def setUp(self):
        """
        Set object level vars
        """
        self.PMID = 26588162
        self.loader = PubmedLoader()

    @pytest.fixture(autouse=True)
    def mock_to_record_with_exception(self, mocker):

        def raise_exception(self, msg):
            raise PMIDLoaderError('Patched PMIDLoaderError')

        mocker.patch.object(PubmedLoader, 'to_record', raise_exception)

    def test_load_records_with_to_record_exception(self):

        with pytest.raises(PMIDLoaderError):
            self.loader.load_records(PMIDs=self.PMID)


@pytest.mark.django_db
class DOILoaderTests(TestCase):
    """
    Tests for the doi loader
    """
    def setUp(self):
        """
        Set object level vars
        """
        self.doi = '10.1021/ct500592m'
        self.loader = DOILoader()

    def test_load_records_from_an_existing_doi(self):
        """Test single import given an existing DOI"""

        self.loader.load_records(DOIs=[self.doi, ])

        self.assertEqual(len(self.loader.records), 1)

        record = self.loader.records[0]
        expected = {
            'title': (
                'Improved PEP-FOLD Approach for Peptide and Miniprotein '
                'Structure Prediction'
            ),
            'authors': [
                {
                    'first_name': 'Yimin',
                    'last_name': 'Shen'
                },
                {
                    'first_name': 'Julien',
                    'last_name': 'Maupetit'
                },
                {
                    'first_name': 'Philippe',
                    'last_name': 'Derreumaux'
                },
                {
                    'first_name': 'Pierre',
                    'last_name': 'Tufféry'
                }
            ],
            'journal': 'Journal of Chemical Theory and Computation',
            'volume': '10',
            'number': '10',
            'pages': '4745-4758',
            'year': 2014,
            'publication_date': datetime.date(2014, 10, 14),
            'is_partial_publication_date': False
        }
        self.assertEqual(record['title'], expected['title'])
        self.assertEqual(record['authors'], expected['authors'])
        self.assertEqual(record['journal'], expected['journal'])
        self.assertEqual(record['volume'], expected['volume'])
        self.assertEqual(record['number'], expected['number'])
        self.assertEqual(record['pages'], expected['pages'])
        self.assertEqual(record['year'], expected['year'])
        self.assertEqual(
            record['publication_date'],
            expected['publication_date']
        )
        self.assertEqual(
            record['is_partial_publication_date'],
            expected['is_partial_publication_date']
        )

    def test_load_records_given_a_fake_string_as_doi(self):
        """Test single import given a fake DOI"""

        with pytest.raises(HTTPError):
            self.loader.load_records(DOIs=['fakeDOI', ])
        self.assertEqual(len(self.loader.records), 0)

    def test_save_records_from_an_existing_doi(self):
        """Test single import given an existing DOI"""

        self.assertEqual(Author.objects.count(), 0)
        self.assertEqual(Entry.objects.count(), 0)
        self.assertEqual(Journal.objects.count(), 0)

        self.loader.load_records(DOIs=[self.doi, ])
        self.loader.save_records()

        self.assertEqual(Author.objects.count(), 4)
        self.assertEqual(Entry.objects.count(), 1)
        self.assertEqual(Journal.objects.count(), 1)

    def test_save_records_from_two_dois(self):
        """Test single import given an existing DOI"""

        self.assertEqual(Author.objects.count(), 0)
        self.assertEqual(Entry.objects.count(), 0)
        self.assertEqual(Journal.objects.count(), 0)

        DOIs = ['10.1093/nar/gks419', '10.1093/nar/gkp323']
        self.loader.load_records(DOIs=DOIs)
        self.loader.save_records()

        self.assertEqual(Author.objects.count(), 6)
        self.assertEqual(Entry.objects.count(), 2)
        self.assertEqual(Journal.objects.count(), 1)

    def test_save_records_from_several_dois(self):
        """Test batch import from a DOI list"""

        self.assertEqual(Entry.objects.count(), 0)

        self.loader.load_records(DOIs=FDOIS)
        self.loader.save_records()

        self.assertEqual(Entry.objects.count(), len(FDOIS))


@pytest.mark.django_db
class DOILoaderToRecordTests(TestCase):
    """
    Tests for the patched pubmed loader
    """
    def setUp(self):
        """
        Set object level vars
        """
        self.doi = '10.1021/ct500592m'
        self.loader = DOILoader()

    @pytest.fixture(autouse=True)
    def mock_to_record_with_exception(self, mocker):

        def raise_exception(self, msg):
            raise DOILoaderError('Patched DOILoaderError')

        mocker.patch.object(DOILoader, 'to_record', raise_exception)

    def test_load_records_with_to_record_exception(self):

        with pytest.raises(DOILoaderError):
            self.loader.load_records(DOIs=self.doi)
