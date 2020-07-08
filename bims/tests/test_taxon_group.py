# coding=utf-8
"""Test Taxon Group."""
from django.test import TestCase
from bims.api_views.taxon_group import (
    update_taxon_group_orders,
    remove_taxa_from_taxon_group
)
from bims.tests.model_factories import (
    TaxonGroupF,
    TaxonomyF,
    BiologicalCollectionRecordF
)
from bims.models.taxon_group import TaxonGroup
from bims.models.biological_collection_record import BiologicalCollectionRecord


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


    def test_remove_taxa_from_taxon_group(self):
        taxonomy_1 = TaxonomyF.create()
        taxonomy_2 = TaxonomyF.create()
        taxonomy_3 = TaxonomyF.create()
        taxon_group_1 = TaxonGroupF.create(
            taxonomies=(taxonomy_1, taxonomy_2)
        )
        biological_1 = BiologicalCollectionRecordF.create(
            taxonomy=taxonomy_1,
            module_group=taxon_group_1
        )
        BiologicalCollectionRecordF.create(
            taxonomy=taxonomy_3,
            module_group=taxon_group_1
        )
        self.assertEqual(taxon_group_1.taxonomies.all().count(), 2)
        self.assertEqual(biological_1.module_group, taxon_group_1)
        remove_taxa_from_taxon_group(
            [taxonomy_1.id],
            taxon_group_1.id
        )
        # Removing taxon that doesn't exist in the group
        remove_taxa_from_taxon_group(
            [taxonomy_3.id],
            taxon_group_1.id
        )
        self.assertEqual(
            TaxonGroup.objects.get(
                id=taxon_group_1.id).taxonomies.all().count(),
            1
        )
        self.assertEqual(
            TaxonGroup.objects.get(
                id=taxon_group_1.id).taxonomies.all().count(),
            1
        )
        self.assertFalse(
            BiologicalCollectionRecord.objects.filter(
                module_group=taxon_group_1
            ).exists()
        )
