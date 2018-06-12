# -*- coding: utf-8 -*-
import datetime
import pytest

from django.core.urlresolvers import reverse
from django.test import TestCase

from ..factories import EntryFactory


@pytest.mark.django_db
class PublicationDateFilterTests(TestCase):
    """Tests for the publication_date filter"""
    def setUp(self):
        """Setup a publication database"""
        # Standard entries
        for i in range(4):
            EntryFactory(is_partial_publication_date=False)

        # Special entry with an incomplete publication date
        EntryFactory(
            publication_date=datetime.date(1980, 1, 1),
            is_partial_publication_date=True,
        )
        self.url = reverse('td_biblio:entry_list')

    def test_publication_date_filter(self):
        """Core testing"""
        response = self.client.get(self.url)

        publication_date_block = '<span class="publication_date">'
        self.assertContains(response, publication_date_block, count=5)

        publication_date_block = '<span class="publication_date">1980.</span>'
        self.assertContains(
            response, publication_date_block, count=1, html=True
        )
