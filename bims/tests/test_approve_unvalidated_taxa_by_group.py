from __future__ import annotations

from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.contrib.sites.models import Site
from django.test import TestCase
from django.urls import reverse

from django_tenants.test.cases import FastTenantTestCase
from django_tenants.test.client import TenantClient

from bims.models import TaxonGroup, TaxonomyUpdateProposal, TaxonGroupTaxonomy
from bims.tasks import approve_unvalidated_taxa_by_group

# Factory shortcuts (adjust imports if your factories live elsewhere)
from bims.tests.model_factories import TaxonomyF, TaxonGroupF

User = get_user_model()


class ApproveUnvalidatedTaxaByGroupTaskTest(FastTenantTestCase):
    """Task-level tests (run task synchronously via .run())."""

    def setUp(self):
        self.client = TenantClient(self.tenant)

        # Actor/expert
        self.user = User.objects.create_user(
            username="expert",
            email="expert@example.com",
            password="pwd",
            is_staff=True,
        )

        # Groups
        self.root_group: TaxonGroup = TaxonGroupF.create(
            site=Site.objects.get_current(),
            category="SPECIES_MODULE",
            name="RootGroup",
            experts=(self.user,),
        )
        self.child_group: TaxonGroup = TaxonGroupF.create(
            site=Site.objects.get_current(),
            category="SPECIES_MODULE",
            name="ChildGroup",
            parent=self.root_group,
            experts=(self.user,),
        )

        # Taxa
        self.taxon_root_unvalidated = TaxonomyF.create(canonical_name="TaxonRoot", validated=False)
        self.taxon_child_unvalidated = TaxonomyF.create(canonical_name="TaxonChild", validated=False)
        self.taxon_validated = TaxonomyF.create(canonical_name="TaxonOK", validated=True)

        # Link taxon ↔ groups
        # root: unvalidated link
        TaxonGroupTaxonomy.objects.create(
            taxongroup=self.root_group,
            taxonomy=self.taxon_root_unvalidated,
            is_validated=False,
            is_rejected=False,
        )
        # child: unvalidated link
        TaxonGroupTaxonomy.objects.create(
            taxongroup=self.child_group,
            taxonomy=self.taxon_child_unvalidated,
            is_validated=False,
            is_rejected=False,
        )
        # validated link (should be ignored)
        TaxonGroupTaxonomy.objects.create(
            taxongroup=self.root_group,
            taxonomy=self.taxon_validated,
            is_validated=True,
            is_rejected=False,
        )

    def test_task_creates_missing_proposals_and_approves_them_including_children(self):
        """Creates proposals when missing and approves them for root + children."""
        # No pre-existing proposals
        self.assertEqual(TaxonomyUpdateProposal.objects.count(), 0)

        # Run task synchronously
        msg = approve_unvalidated_taxa_by_group.run(
            taxon_group_id=self.root_group.id,
            initiated_by_user_id=self.user.id,
            include_children=True,
        )
        self.assertIn("Unvalidated taxa processed", msg)

        # Proposals created for the two unvalidated links
        self.assertEqual(TaxonomyUpdateProposal.objects.count(), 2)

        # Each proposal should be approved
        statuses = set(
            TaxonomyUpdateProposal.objects.values_list("status", flat=True)
        )
        self.assertEqual(statuses, {"approved"})

        # Sanity: proposals paired with the expected taxa/groups
        exists_root = TaxonomyUpdateProposal.objects.filter(
            original_taxonomy_id=self.taxon_root_unvalidated.id,
            taxon_group_id=self.root_group.id,
            status="approved",
        ).exists()
        exists_child = TaxonomyUpdateProposal.objects.filter(
            original_taxonomy_id=self.taxon_child_unvalidated.id,
            taxon_group_id=self.child_group.id,
            status="approved",
        ).exists()
        self.assertTrue(exists_root)
        self.assertTrue(exists_child)

    def test_task_without_include_children_ignores_child_group(self):
        """When include_children=False, only root group's unvalidated links are processed."""
        approve_unvalidated_taxa_by_group.run(
            taxon_group_id=self.root_group.id,
            initiated_by_user_id=self.user.id,
            include_children=False,
        )

        # Only 1 proposal (for the root)
        self.assertEqual(TaxonomyUpdateProposal.objects.count(), 1)
        self.assertTrue(
            TaxonomyUpdateProposal.objects.filter(
                original_taxonomy_id=self.taxon_root_unvalidated.id,
                taxon_group_id=self.root_group.id,
                status="approved",
            ).exists()
        )
        self.assertFalse(
            TaxonomyUpdateProposal.objects.filter(
                original_taxonomy_id=self.taxon_child_unvalidated.id,
                taxon_group_id=self.child_group.id,
            ).exists()
        )

    def test_task_returns_no_work_message_when_nothing_to_process(self):
        """If no unvalidated links, task should return an early no-op message."""
        # Make everything validated
        TaxonGroupTaxonomy.objects.update(is_validated=True)

        msg = approve_unvalidated_taxa_by_group.run(
            taxon_group_id=self.root_group.id,
            initiated_by_user_id=self.user.id,
        )
        self.assertIn("No unvalidated taxa found", msg)


class ApproveUnvalidatedTaxaByGroupAPIViewTest(FastTenantTestCase):
    """API view tests – permission and queuing behavior."""

    def setUp(self):
        self.client = TenantClient(self.tenant)

        self.user_expert = User.objects.create_user(
            username="expert",
            email="expert@example.com",
            password="pwd",
        )
        self.user_non_expert = User.objects.create_user(
            username="nope",
            email="nope@example.com",
            password="pwd",
        )

        self.group: TaxonGroup = TaxonGroupF.create(
            site=Site.objects.get_current(),
            category="SPECIES_MODULE",
            name="APIGroup",
            experts=(self.user_expert,),
        )

        # Make a couple of unvalidated links so the endpoint is meaningful
        tx = TaxonomyF.create(canonical_name="APITaxon", validated=False)
        TaxonGroupTaxonomy.objects.create(
            taxongroup=self.group,
            taxonomy=tx,
            is_validated=False,
            is_rejected=False,
        )

    def test_non_authenticated_is_rejected(self):
        url = reverse("approve-group-proposals")
        resp = self.client.post(url, data={"taxon_group_id": self.group.id}, content_type="application/json")
        # DRF IsAuthenticated returns 401 for unauthenticated
        self.assertIn(resp.status_code, (401, 403))

    def test_non_expert_gets_403(self):
        self.client.login(username="nope", password="pwd")
        url = reverse("approve-group-proposals")
        resp = self.client.post(url, data={"taxon_group_id": self.group.id}, content_type="application/json")
        self.assertEqual(resp.status_code, 403)

    @patch("bims.api_views.taxon.approve_unvalidated_taxa_by_group.delay")
    def test_expert_gets_202_and_task_is_queued(self, mock_delay):
        self.client.login(username="expert", password="pwd")
        mock_delay.return_value = type("FakeAsync", (), {"id": "abc123"})()

        url = reverse("approve-group-proposals")
        resp = self.client.post(
            url,
            data={"taxon_group_id": self.group.id, "include_children": True},
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 202)
        self.assertEqual(resp.json()["task_id"], "abc123")

        mock_delay.assert_called_once_with(
            taxon_group_id=self.group.id,
            initiated_by_user_id=self.user_expert.id,
            include_children=True,
        )
