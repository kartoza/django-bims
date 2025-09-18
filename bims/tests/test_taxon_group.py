# coding=utf-8
"""Test Taxon Group."""
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission, Group
from django.contrib.sites.models import Site
from django.test import TestCase
from rest_framework.test import force_authenticate, APIRequestFactory

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
from mobile.api_views.taxon_group import TaxonGroupTotalValidated


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


class TestTaxonGroupTotalValidated(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        User = get_user_model()
        self.superuser = User.objects.create_superuser(
            username="admin",
            email="admin@example.com",
            password="x",
        )
        self.user = User.objects.create_user(
            username="user",
            email="user@example.com",
            password="x",
        )

    def _link(self, group, taxonomy, *, is_validated=True):
        """
        Attach a taxonomy to a taxon group with the is_validated flag.
        Works for explicit-through M2M using through_defaults.
        """
        group.taxonomies.add(taxonomy, through_defaults={"is_validated": is_validated})

    def _call(self, group, user):
        view = TaxonGroupTotalValidated.as_view()
        req = self.factory.get(f"/fake/taxon-group/{group.id}/totals/")
        force_authenticate(req, user=user)
        resp = view(req, id=group.id)
        self.assertEqual(resp.status_code, 200)
        return resp.data

    def test_superuser_sees_all_buckets(self):
        # Parent group
        tg = TaxonGroupF.create()

        # Accepted validated (ACCEPTED, DOUBTFUL, and BLANK should count as accepted)
        t_acc = TaxonomyF.create(taxonomic_status="ACCEPTED")
        t_doubt = TaxonomyF.create(taxonomic_status="DOUBTFUL")
        t_blank = TaxonomyF.create(taxonomic_status="")  # blank -> accepted

        # Synonym validated
        t_syn = TaxonomyF.create(taxonomic_status="SYNONYM")

        # Unvalidated
        t_acc_u = TaxonomyF.create(taxonomic_status="ACCEPTED")
        t_syn_u = TaxonomyF.create(taxonomic_status="MISAPPLIED")  # synonym subclass

        # Link them with validation flags
        self._link(tg, t_acc, is_validated=True)
        self._link(tg, t_doubt, is_validated=True)
        self._link(tg, t_blank, is_validated=True)
        self._link(tg, t_syn, is_validated=True)

        self._link(tg, t_acc_u, is_validated=False)
        self._link(tg, t_syn_u, is_validated=False)

        data = self._call(tg, self.superuser)

        self.assertEqual(data["accepted_validated"], 3)     # acc + doubtful + blank
        self.assertEqual(data["synonym_validated"], 1)      # synonym
        self.assertEqual(data["accepted_unvalidated"], 1)   # acc_u
        self.assertEqual(data["synonym_unvalidated"], 1)    # misapplied

        self.assertEqual(data["total_validated"], 4)
        self.assertEqual(data["total_unvalidated"], 2)

    def test_regular_user_hides_unvalidated_counts(self):
        tg = TaxonGroupF.create()

        t_acc = TaxonomyF.create(taxonomic_status="ACCEPTED")
        t_syn = TaxonomyF.create(taxonomic_status="SYNONYM")
        t_acc_u = TaxonomyF.create(taxonomic_status="ACCEPTED")
        t_syn_u = TaxonomyF.create(taxonomic_status="HOMOTYPIC_SYNONYM")

        self._link(tg, t_acc, is_validated=True)
        self._link(tg, t_syn, is_validated=True)
        self._link(tg, t_acc_u, is_validated=False)
        self._link(tg, t_syn_u, is_validated=False)

        data = self._call(tg, self.user)

        # Validated visible
        self.assertEqual(data["accepted_validated"], 1)
        self.assertEqual(data["synonym_validated"], 1)
        self.assertEqual(data["total_validated"], 2)

        # Unvalidated hidden for non-expert/non-superuser
        self.assertEqual(data["accepted_unvalidated"], 0)
        self.assertEqual(data["synonym_unvalidated"], 0)
        self.assertEqual(data["total_unvalidated"], 0)

    def test_recurses_into_children(self):
        parent = TaxonGroupF.create()
        child = TaxonGroupF.create(parent=parent)

        # Put everything on the child and assert parent includes them
        t_acc = TaxonomyF.create(taxonomic_status="DOUBTFUL")  # accepted bucket
        t_syn = TaxonomyF.create(taxonomic_status="PROPARTE_SYNONYM")

        self._link(child, t_acc, is_validated=True)
        self._link(child, t_syn, is_validated=False)

        data_super = self._call(parent, self.superuser)
        self.assertEqual(data_super["accepted_validated"], 1)
        self.assertEqual(data_super["synonym_unvalidated"], 1)
        self.assertEqual(data_super["total_validated"], 1)
        self.assertEqual(data_super["total_unvalidated"], 1)

        data_user = self._call(parent, self.user)
        self.assertEqual(data_user["accepted_validated"], 1)
        self.assertEqual(data_user["synonym_unvalidated"], 0)  # hidden
        self.assertEqual(data_user["total_unvalidated"], 0)
