# coding=utf-8
"""Test Taxon Group."""
from django.contrib.auth.models import Permission, Group
from django.contrib.sites.models import Site
from django.test import TestCase
from bims.api_views.taxon_group import (
    update_taxon_group_orders,
    remove_taxa_from_taxon_group,
    add_taxa_to_taxon_group
)
from bims.tests.model_factories import (
    TaxonGroupF,
    TaxonomyF,
    BiologicalCollectionRecordF
)
from bims.models.taxon_group import (
    TaxonGroup, TAXON_GROUP_LEVEL_1,
    TAXON_GROUP_LEVEL_3, TAXON_GROUP_LEVEL_2
)
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
        update_taxon_group_orders([2, 1])
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

    def test_add_taxa_to_taxon_group(self):
        taxonomy_1 = TaxonomyF.create()
        taxonomy_2 = TaxonomyF.create()
        BiologicalCollectionRecordF.create(
            taxonomy=taxonomy_1
        )
        taxon_group_1 = TaxonGroupF.create()
        add_taxa_to_taxon_group(
            [taxonomy_1.id, taxonomy_2.id],
            taxon_group_1.id
        )
        self.assertEqual(
            TaxonGroup.objects.get(
                id=taxon_group_1.id).taxonomies.all().count(),
            2
        )

    def test_add_taxon_group_level_2(self):
        taxon_group = TaxonGroupF.create(
            level=TAXON_GROUP_LEVEL_2,
            site=Site.objects.get_current()
        )
        self.assertTrue(
            Permission.objects.filter(
                name=taxon_group.permission_name
            ).exists()
        )
        self.assertTrue(
            Group.objects.filter(
                name=taxon_group.group_name
            ).exists()
        )
        self.assertTrue(str(taxon_group), f'{taxon_group.name} - {taxon_group.level}')

    def test_add_taxon_group_level_3(self):
        ancestor_taxon_group = TaxonGroupF.create(
            level=TAXON_GROUP_LEVEL_1,
            site=Site.objects.get_current()
        )
        parent_taxon_group = TaxonGroupF.create(
            level=TAXON_GROUP_LEVEL_2,
            site=Site.objects.get_current(),
            parent=ancestor_taxon_group
        )
        taxon_group = TaxonGroupF.create(
            level=TAXON_GROUP_LEVEL_3,
            site=Site.objects.get_current(),
            parent=parent_taxon_group
        )
        child_permission = Permission.objects.filter(
            name=taxon_group.permission_name
        ).first()
        parent_permission = Permission.objects.filter(
            name=parent_taxon_group.permission_name
        )
        parent_group = Group.objects.filter(
            name=parent_taxon_group.group_name
        ).first()
        self.assertIsNotNone(parent_permission)
        self.assertTrue(
            Group.objects.filter(
                name=taxon_group.group_name
            ).exists()
        )
        self.assertTrue(
            parent_group.permissions.filter(
                id__in=[child_permission.id]
            ).exists()
        )

    def test_add_taxon_group_level_3_without_site(self):
        taxon_group = TaxonGroupF.create(
            level=TAXON_GROUP_LEVEL_3,
            site=None
        )
        self.assertFalse(
            Permission.objects.filter(
                name=taxon_group.permission_name
            ).exists()
        )

    def test_update_taxon_group(self):
        taxon_group = TaxonGroupF.create(
            name='test1',
            level=TAXON_GROUP_LEVEL_3,
            site=Site.objects.get_current()
        )
        self.assertTrue(
            'test1' in Permission.objects.filter(
                name=taxon_group.permission_name
            ).first().name
        )
        taxon_group.name = 'test2'
        taxon_group.save()
        self.assertFalse(
            'test1' in Permission.objects.filter(
                name=taxon_group.permission_name
            ).first().name
        )

