from django.urls import reverse
from django.test import TestCase
from django_tenants.test.cases import FastTenantTestCase
from django_tenants.test.client import TenantClient
from rest_framework import status
from django.contrib.auth import get_user_model
from bims.models.taxonomy_update_proposal import (
    TaxonomyUpdateProposal,
    TaxonomyUpdateReviewer
)
from bims.models.taxonomy import Taxonomy
from bims.tests.model_factories import (
    TaxonomyF,
    TaxonGroupF,
    TaxonomyUpdateProposalF
)

User = get_user_model()


class ReviewTaxonProposalTest(FastTenantTestCase):
    def setUp(self):
        self.expert_user = User.objects.create_user('testuser', 'test@example.com', 'password')
        self.normal_user = User.objects.create_user('normal_user',
                                                    'normal_user@example.com', 'password')
        self.user_2 = User.objects.create_user('user_2', 'user_2@example.com', 'password')
        self.client = TenantClient(self.tenant)
        self.superuser = User.objects.create_user(
            username='superuser',
            email='superuser@example.com',
            password='password',
            is_superuser=True
        )
        self.taxonomy = TaxonomyF.create(
            scientific_name='Test Name',
            canonical_name='Test Canonical Name')
        self.taxon_group = TaxonGroupF.create(
            name='Test Group',
            taxonomies=(self.taxonomy,),
            experts=(self.expert_user,)
        )

    def test_superuser_approve_update_taxon(self):
        self.client.login(username='superuser', password='password')
        taxonomy_update_proposal = TaxonomyUpdateProposalF.create(
            scientific_name='Updated Test Name',
            canonical_name='Updated Test Canonical Name',
            original_taxonomy=self.taxonomy,
            taxon_group=self.taxon_group
        )

        url = reverse('review-taxon-proposal',
                      kwargs={
                          'taxonomy_update_proposal_id': taxonomy_update_proposal.pk,
                      })

        response = self.client.put(url, {
            'action': 'approve'
        }, content_type='application/json')

        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)

        updated_taxonomy = Taxonomy.objects.get(
            id=self.taxonomy.id
        )
        self.assertEqual(updated_taxonomy.scientific_name, 'Updated Test Name')
        self.assertEqual(updated_taxonomy.canonical_name, 'Updated Test Canonical Name')
        self.assertTrue(
            TaxonomyUpdateProposal.objects.filter(
                id=taxonomy_update_proposal.id,
                reviewers__in=[self.superuser],
            ).exists()
        )

        self.client.logout()

    def test_parent_expert_approve_update_taxon(self):
        self.taxon_group_level_2 = TaxonGroupF.create(
            name='Test Group',
            parent=self.taxon_group,
            experts=(self.normal_user, )
        )
        self.taxon_group_level_3 = TaxonGroupF.create(
            name='Test Group',
            parent=self.taxon_group_level_2,
            experts=(self.user_2, )
        )
        taxonomy_update_proposal = TaxonomyUpdateProposalF.create(
            scientific_name='Updated Test Name',
            canonical_name='Updated Test Canonical Name',
            original_taxonomy=self.taxonomy,
            taxon_group=self.taxon_group_level_3
        )
        self.client.login(username='normal_user', password='password')
        url = reverse('review-taxon-proposal',
                      kwargs={
                          'taxonomy_update_proposal_id': taxonomy_update_proposal.pk
                      })

        response = self.client.put(url, {
            'action': 'approve'
        }, content_type='application/json')

        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)

        updated_taxonomy = Taxonomy.objects.get(
            id=self.taxonomy.id
        )
        self.assertFalse(TaxonomyUpdateProposal.objects.filter(
            status='approved',
            id=taxonomy_update_proposal.id
        ).exists())
        self.assertNotEqual(updated_taxonomy.scientific_name, 'Updated Test Name')
        self.assertNotEqual(updated_taxonomy.canonical_name, 'Updated Test Canonical Name')

        self.client.logout()

        self.client.login(username='testuser', password='password')
        url = reverse('review-taxon-proposal',
                      kwargs={
                          'taxonomy_update_proposal_id': taxonomy_update_proposal.pk
                      })

        response = self.client.put(url, {
            'action': 'approve'
        }, content_type='application/json')

        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)

        updated_taxonomy = Taxonomy.objects.get(
            id=self.taxonomy.id
        )
        self.assertTrue(TaxonomyUpdateProposal.objects.filter(
            status='approved',
            id=taxonomy_update_proposal.id
        ).exists())
        self.assertEqual(updated_taxonomy.scientific_name, 'Updated Test Name')
        self.assertEqual(updated_taxonomy.canonical_name, 'Updated Test Canonical Name')

        self.client.logout()

    def test_expert_reject_taxon(self):
        taxonomy_update_proposal = TaxonomyUpdateProposalF.create(
            scientific_name='Updated Test Name',
            canonical_name='Updated Test Canonical Name',
            original_taxonomy=self.taxonomy,
            taxon_group=self.taxon_group
        )
        self.client.login(username='testuser', password='password')
        url = reverse('review-taxon-proposal',
                      kwargs={
                          'taxonomy_update_proposal_id': taxonomy_update_proposal.pk
                      })

        response = self.client.put(url, {
            'action': 'reject',
            'comments': 'test'
        }, content_type='application/json')

        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
        self.assertTrue(TaxonomyUpdateProposal.objects.filter(
            status='rejected',
            id=taxonomy_update_proposal.id,
        ).exists())
        self.assertTrue(TaxonomyUpdateReviewer.objects.filter(
            taxonomy_update_proposal=taxonomy_update_proposal,
            reviewer__username='testuser',
            comments='test'
        ).exists())
        self.client.logout()
