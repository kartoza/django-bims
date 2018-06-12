# -*- coding: utf-8 -*-
"""
Django TailorDev Biblio

Test forms
"""
from __future__ import unicode_literals
from django.test import TestCase

from ..forms import text_to_list, EntryBatchImportForm


def test_text_to_list():
    """Test text_to_list utils"""
    inputs = [
        'foo,bar,lol',
        'foo , bar, lol',
        'foo\nbar\nlol',
        'foo,\nbar,\nlol',
        'foo, \nbar,lol',
        'foo,,bar,\nlol',
    ]
    expected = ['bar', 'foo', 'lol']

    for input in inputs:
        result = text_to_list(input)
        result.sort()
        assert result == expected


class EntryBatchImportFormTests(TestCase):
    """
    Tests for the EntryBatchImportForm
    """

    def test_clean_pmids(self):
        """Test PMIDs cleaning method"""

        inputs = [
            {'pmids': '26588162\n19569182'},
            {'pmids': '19569182\n26588162'},
            {'pmids': '19569182,\n26588162'},
            {'pmids': '19569182,26588162'},
            {'pmids': '19569182,,26588162'},
            {'pmids': '19569182\n\n26588162'},
        ]
        expected = ['19569182', '26588162']

        for input in inputs:

            form = EntryBatchImportForm(input)
            assert form.is_valid()

            pmids = form.cleaned_data['pmids']
            pmids.sort()
            assert pmids == expected

    def test_clean_pmids_with_random_input(self):
        """Test PMIDs cleaning method with non PMIDs"""
        inputs = [
            {'pmids': 'lorem, ipsum'},
            {'pmids': 'lorem, 19569182'},
            {'pmids': 'lorem42\nipsum234'},
        ]

        for input in inputs:
            form = EntryBatchImportForm(input)
            self.assertFalse(form.is_valid())

    def test_clean_dois(self):
        """Test DOIs cleaning method"""

        inputs = [
            {'dois': '10.1093/nar/gks419\n10.1093/nar/gkp323'},
            {'dois': '10.1093/nar/gkp323\n10.1093/nar/gks419'},
            {'dois': '10.1093/nar/gkp323,\n10.1093/nar/gks419'},
            {'dois': '10.1093/nar/gkp323,10.1093/nar/gks419'},
            {'dois': '10.1093/nar/gkp323,,10.1093/nar/gks419'},
            {'dois': '10.1093/nar/gkp323\n\n10.1093/nar/gks419'},
        ]
        expected = ['10.1093/nar/gkp323', '10.1093/nar/gks419']

        for input in inputs:

            form = EntryBatchImportForm(input)
            assert form.is_valid()

            dois = form.cleaned_data['dois']
            dois.sort()
            assert dois == expected

    def test_clean_dois_with_random_input(self):
        """Test DOIs cleaning method with non DOIs"""
        inputs = [
            {'dois': 'lorem, ipsum'},
            {'dois': 'lorem, 19569182'},
            {'dois': 'lorem42\nipsum234'},
        ]

        for input in inputs:
            form = EntryBatchImportForm(input)
            self.assertFalse(form.is_valid())

    def test_clean_with_pmids_and_dois(self):
        """Test clean method with DOIs & PMIDs"""

        data = {
            'dois': '10.1093/nar/gks419\n10.1093/nar/gkp323',
            'pmids': '26588162\n19569182',
        }

        expected = {
            'dois': ['10.1093/nar/gkp323', '10.1093/nar/gks419'],
            'pmids': ['19569182', '26588162'],
        }

        form = EntryBatchImportForm(data)
        self.assertTrue(form.is_valid())
        self.assertDictEqual(expected, form.cleaned_data)

    def test_clean_without_pmids_or_dois(self):
        """Test clean method without DOIs or PMIDs"""

        data = {
            'dois': '',
            'pmids': '',
        }

        form = EntryBatchImportForm(data)
        self.assertFalse(form.is_valid())
