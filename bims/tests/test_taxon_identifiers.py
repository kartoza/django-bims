# coding=utf-8
"""Test Taxon Identifiers."""

from django.test import TransactionTestCase
from bims.utils.gbif import process_taxon_identifier


class TestTaxonIdentifier(TransactionTestCase):
    """Test Taxon Identifier."""

    def test_process_taxon(self):
        taxon_identifier = process_taxon_identifier(121)
        self.assertIsNotNone(taxon_identifier)

    def test_get_all_parent(self):
        gbif_key = 204
        taxon_identifier = process_taxon_identifier(gbif_key)
        parent = 0
        while taxon_identifier.parent:
            self.assertIsNotNone(taxon_identifier.parent)
            parent += 1
            taxon_identifier = taxon_identifier.parent
        self.assertTrue(parent == 2)
