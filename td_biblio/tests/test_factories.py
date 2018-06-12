# -*- coding: utf-8 -*-
"""
TailorDev Bibliography

Test factories.
"""
import pytest
from django.test import TestCase

from ..factories import FuzzyPages, EntryFactory


@pytest.mark.django_db
class FuzzyPagesTestCase(TestCase):

    def test_simple_call(self):
        """Test the Fuzzy pages attribute implicit call"""

        entry = EntryFactory()
        self.assertNotEqual(len(entry.pages), 0)

    def test_only_max_page(self):
        """Test the Fuzzy pages attribute explicit call"""

        entry = EntryFactory(pages=FuzzyPages(1, 10))
        page_min, page_max = map(int, entry.pages.split('--'))
        self.assertNotEqual(len(entry.pages), 0)
        self.assertLessEqual(page_min, 10)
        self.assertGreaterEqual(page_min, 1)
        self.assertLessEqual(page_max, 10)
        self.assertGreaterEqual(page_max, 1)

        entry = EntryFactory(pages=FuzzyPages(10))
        page_min, page_max = map(int, entry.pages.split('--'))
        self.assertNotEqual(len(entry.pages), 0)
        self.assertLessEqual(page_min, 10)
        self.assertGreaterEqual(page_min, 1)
        self.assertLessEqual(page_max, 10)
        self.assertGreaterEqual(page_max, 1)
