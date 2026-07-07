# coding=utf-8
from unittest.mock import MagicMock, patch

from django.test import TestCase

from bims.tasks.citation_download import (
    _absolute_url,
    _bibtex_authors,
    _bibtex_key,
    _dataset_url,
    _format_bibtex,
    _format_dataset,
    _format_dataset_bibtex,
    _format_dataset_plain,
    _format_dataset_ris,
    _format_plain,
    _format_ris,
    _parse_dataset_author_year,
)
from bims.tests.model_factories import DatasetF


# ------------------------------------------------------------------ #
# _bibtex_authors
# ------------------------------------------------------------------ #

class TestBibtexAuthors(TestCase):

    def test_ampersand_replaced_with_and(self):
        result = _bibtex_authors('Barry Clark & Dean Impson')
        self.assertEqual(result, 'Barry Clark and Dean Impson')

    def test_comma_replaced_with_and(self):
        result = _bibtex_authors('Barry Clark, Dean Impson, Johannes Rall')
        self.assertEqual(result, 'Barry Clark and Dean Impson and Johannes Rall')

    def test_mixed_separators(self):
        result = _bibtex_authors('Barry Clark, Dean Impson & Johannes Rall')
        self.assertEqual(result, 'Barry Clark and Dean Impson and Johannes Rall')

    def test_single_author(self):
        self.assertEqual(_bibtex_authors('Dave Christie'), 'Dave Christie')

    def test_empty_string(self):
        self.assertEqual(_bibtex_authors(''), '')


# ------------------------------------------------------------------ #
# _bibtex_key
# ------------------------------------------------------------------ #

class TestBibtexKey(TestCase):

    def _make_ref(self, authors='', year=None, title=''):
        ref = MagicMock()
        ref.authors = authors
        ref.year = year
        ref.title = title
        return ref

    def test_basic_key(self):
        ref = self._make_ref('Barry Clark, Dean Impson', 2009, 'Present status')
        self.assertEqual(_bibtex_key(ref), 'Clark2009present')

    def test_ampersand_in_authors(self):
        ref = self._make_ref('Barry Clark & Dean Impson', 2009, 'Present status')
        self.assertEqual(_bibtex_key(ref), 'Clark2009present')

    def test_comma_stripped_from_title_first_word(self):
        ref = self._make_ref('Roger Bills', 1999, 'Bills, I.R. 1999. Biology')
        key = _bibtex_key(ref)
        self.assertNotIn(',', key)

    def test_no_year(self):
        ref = self._make_ref('Someone', None, 'A title')
        self.assertIn('nd', _bibtex_key(ref))

    def test_unpublished_data_title_gives_empty_word(self):
        ref = self._make_ref('Someone', 2020, 'Unpublished data')
        self.assertEqual(_bibtex_key(ref), 'Someone2020')

    def test_key_contains_only_word_chars(self):
        ref = self._make_ref('Author', 2020, 'Observation.org, title')
        key = _bibtex_key(ref)
        self.assertRegex(key, r'^\w+$')


# ------------------------------------------------------------------ #
# _absolute_url
# ------------------------------------------------------------------ #

class TestAbsoluteUrl(TestCase):

    @patch('bims.tasks.citation_download.get_current_domain', return_value='fbis.example.com')
    def test_relative_url_gets_host(self, _mock):
        result = _absolute_url('/uploaded/docs/file.pdf')
        self.assertEqual(result, 'https://fbis.example.com/uploaded/docs/file.pdf')

    def test_absolute_url_unchanged(self):
        url = 'https://hdl.handle.net/10962/d1001668'
        self.assertEqual(_absolute_url(url), url)

    def test_empty_string_unchanged(self):
        self.assertEqual(_absolute_url(''), '')


# ------------------------------------------------------------------ #
# _dataset_url
# ------------------------------------------------------------------ #

class TestDatasetUrl(TestCase):

    def test_bare_doi_prefixed(self):
        dataset = DatasetF.build(url='10.15468/efh2ib')
        self.assertEqual(_dataset_url(dataset), 'https://doi.org/10.15468/efh2ib')

    def test_full_url_unchanged(self):
        dataset = DatasetF.build(url='https://example.com/dataset')
        self.assertEqual(_dataset_url(dataset), 'https://example.com/dataset')

    def test_empty_url(self):
        dataset = DatasetF.build(url='')
        self.assertEqual(_dataset_url(dataset), '')


# ------------------------------------------------------------------ #
# _parse_dataset_author_year
# ------------------------------------------------------------------ #

class TestParseDatasetAuthorYear(TestCase):

    def test_standard_gbif_citation(self):
        dataset = DatasetF.build(citation='Catania D, Fong J (2024). CAS Ichthyology.')
        author, year = _parse_dataset_author_year(dataset)
        self.assertEqual(author, 'Catania D, Fong J')
        self.assertEqual(year, '2024')

    def test_no_citation(self):
        dataset = DatasetF.build(citation='')
        author, year = _parse_dataset_author_year(dataset)
        self.assertEqual(author, '')
        self.assertEqual(year, '')

    def test_citation_without_year_match(self):
        dataset = DatasetF.build(citation='No year here. Some title.')
        author, year = _parse_dataset_author_year(dataset)
        self.assertEqual(author, '')
        self.assertEqual(year, '')


# ------------------------------------------------------------------ #
# _format_bibtex (SourceReference)
# ------------------------------------------------------------------ #

class TestFormatBibtex(TestCase):

    def _make_ref(self, authors='Author A', year=2020, title='A Title', note=None):
        ref = MagicMock()
        ref.authors = authors
        ref.year = year
        ref.title = title
        ref.note = note
        ref.reference_source = None
        ref.is_bibliography.return_value = False
        ref.is_published_report.return_value = False
        ref.is_database.return_value = False
        return ref

    def test_misc_entry_type(self):
        ref = self._make_ref()
        output = _format_bibtex(ref)
        self.assertIn('@misc{', output)

    def test_unpublished_entry_has_note(self):
        ref = self._make_ref(note='Unpublished survey data')
        output = _format_bibtex(ref)
        self.assertIn('@unpublished{', output)
        self.assertIn('note = {Unpublished survey data}', output)

    def test_unpublished_with_dash_note_gets_fallback(self):
        ref = self._make_ref(note='-')
        output = _format_bibtex(ref)
        self.assertIn('note = {Unpublished data}', output)

    def test_authors_use_and_separator(self):
        ref = self._make_ref(authors='Barry Clark, Dean Impson & Johannes Rall')
        output = _format_bibtex(ref)
        self.assertIn('Barry Clark and Dean Impson and Johannes Rall', output)
        self.assertNotIn('&', output)

    def test_key_has_no_comma(self):
        ref = self._make_ref(authors='Roger Bills', year=1999, title='Bills, I.R. 1999.')
        output = _format_bibtex(ref)
        key_line = output.split('\n')[0]
        # key is between @misc{ and ,
        key = key_line.split('{')[1].rstrip(',')
        self.assertNotIn(',', key)

    def test_techreport_has_institution(self):
        ref = self._make_ref()
        ref.is_published_report.return_value = True
        ref.reference_source = 'University of Cape Town'
        doc = MagicMock()
        doc.source.doc_url = 'http://hdl.handle.net/1234'
        doc.source.doc_file = None
        ref.sourcereferencedocument = doc
        output = _format_bibtex(ref)
        self.assertIn('@techreport{', output)
        self.assertIn('institution = {University of Cape Town}', output)

    def test_techreport_institution_fallback_to_author(self):
        ref = self._make_ref(authors='Dave Christie')
        ref.is_published_report.return_value = True
        ref.reference_source = None
        doc = MagicMock()
        doc.source.doc_url = ''
        doc.source.doc_file = None
        ref.sourcereferencedocument = doc
        output = _format_bibtex(ref)
        self.assertIn('institution = {Dave Christie}', output)


# ------------------------------------------------------------------ #
# _format_dataset_bibtex
# ------------------------------------------------------------------ #

class TestFormatDatasetBibtex(TestCase):

    def test_doi_url_used_as_url_field(self):
        dataset = DatasetF.build(
            name='CAS Ichthyology (ICH)',
            citation='Catania D, Fong J (2024). CAS Ichthyology.',
            url='10.15468/efh2ib',
        )
        output = _format_dataset_bibtex(dataset)
        self.assertIn('@misc{', output)
        self.assertIn('publisher = {Global Biodiversity Information Facility (GBIF)}', output)
        self.assertIn('url = {https://doi.org/10.15468/efh2ib}', output)

    def test_authors_use_and_separator(self):
        dataset = DatasetF.build(
            name='Dataset',
            citation='de Moor F, Ranwashe F (2017). AM Dataset.',
            url='10.15468/spzgor',
        )
        output = _format_dataset_bibtex(dataset)
        self.assertIn(' and ', output)
        self.assertNotIn('&', output)

    def test_key_has_no_invalid_chars(self):
        dataset = DatasetF.build(
            name='Observation.org, Nature data',
            citation='',
            url='10.15468/5nilie',
        )
        output = _format_dataset_bibtex(dataset)
        key = output.split('{')[1].split(',')[0]
        self.assertRegex(key, r'^\w+$')

    def test_no_year_field_when_missing(self):
        dataset = DatasetF.build(
            name='Fish Collection NRM',
            citation='',
            url='10.15468/d7eitf',
        )
        output = _format_dataset_bibtex(dataset)
        self.assertNotIn('year =', output)


# ------------------------------------------------------------------ #
# _format_dataset_ris
# ------------------------------------------------------------------ #

class TestFormatDatasetRis(TestCase):

    def test_doi_uses_do_field(self):
        dataset = DatasetF.build(
            name='CAS Ichthyology (ICH)',
            citation='Catania D, Fong J (2024). CAS Ichthyology.',
            url='10.15468/efh2ib',
        )
        output = _format_dataset_ris(dataset)
        self.assertIn('DO  - 10.15468/efh2ib', output)
        self.assertNotIn('UR  -', output)

    def test_non_doi_uses_ur_field(self):
        dataset = DatasetF.build(
            name='Some Dataset',
            citation='Author A (2020). Title.',
            url='https://example.com/dataset',
        )
        output = _format_dataset_ris(dataset)
        self.assertIn('UR  - https://example.com/dataset', output)
        self.assertNotIn('DO  -', output)

    def test_ty_is_data(self):
        dataset = DatasetF.build(name='D', citation='', url='')
        self.assertIn('TY  - DATA', _format_dataset_ris(dataset))

    def test_ends_with_er(self):
        dataset = DatasetF.build(name='D', citation='', url='')
        self.assertIn('ER  - ', _format_dataset_ris(dataset))


# ------------------------------------------------------------------ #
# _format_dataset_plain
# ------------------------------------------------------------------ #

class TestFormatDatasetPlain(TestCase):

    def test_full_citation(self):
        dataset = DatasetF.build(
            name='CAS Ichthyology (ICH)',
            citation='Catania D, Fong J (2024). CAS Ichthyology.',
            url='10.15468/efh2ib',
        )
        output = _format_dataset_plain(dataset)
        self.assertIn('Catania D, Fong J', output)
        self.assertIn('2024', output)
        self.assertIn('CAS Ichthyology (ICH)', output)
        self.assertIn('Global Biodiversity Information Facility (GBIF)', output)
        self.assertIn('https://doi.org/10.15468/efh2ib', output)

    def test_no_author_fallback(self):
        dataset = DatasetF.build(name='Fish Collection NRM', citation='', url='')
        output = _format_dataset_plain(dataset)
        self.assertIn('Unknown', output)
        self.assertIn('n.d.', output)


# ------------------------------------------------------------------ #
# _format_dataset dispatch
# ------------------------------------------------------------------ #

class TestFormatDataset(TestCase):

    def setUp(self):
        self.dataset = DatasetF.build(
            name='CAS Ichthyology (ICH)',
            citation='Catania D, Fong J (2024). CAS Ichthyology.',
            url='10.15468/efh2ib',
        )

    def test_bibtex_dispatch(self):
        output = _format_dataset(self.dataset, 'bibtex')
        self.assertIn('@misc{', output)

    def test_ris_dispatch(self):
        output = _format_dataset(self.dataset, 'ris')
        self.assertIn('TY  - DATA', output)

    def test_plain_dispatch(self):
        output = _format_dataset(self.dataset, 'plain')
        self.assertIn('Global Biodiversity Information Facility', output)
