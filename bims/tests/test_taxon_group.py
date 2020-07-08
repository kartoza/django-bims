# coding=utf-8
"""Test Taxon Group."""
from django.test import TestCase
from bims.api_views.taxon_group import update_taxon_group_orders
from bims.tests.model_factories import TaxonGroupF
from bims.models.taxon_group import TaxonGroup


class TestTaxonGroup(TestCase):
    """Test Taxon Groups."""

    def setUp(self):
        pass

    def test_update_taxon_group_orders(self):
        taxon_group_1 = TaxonGroupF.create(
            id=1,
            display_order=0
        )
        taxon_group_2 = TaxonGroupF.create(
            id=2,
            display_order=1
        )
        self.assertEqual(taxon_group_1.display_order, 0)
        self.assertEqual(taxon_group_2.display_order, 1)
        update_taxon_group_orders([2,1])
        self.assertEqual(TaxonGroup.objects.get(id=1).display_order, 1)
        self.assertEqual(TaxonGroup.objects.get(id=2).display_order, 0)
