from django.urls import reverse
from django.test import TestCase
from rest_framework import status
from django.contrib.auth import get_user_model
from bims.models.taxonomy_update_proposal import TaxonomyUpdateProposal
from bims.models.taxonomy import Taxonomy
from bims.tests.model_factories import (
    TaxonomyF,
    TaxonGroupF,
    TaxonomyUpdateProposalF
)

User = get_user_model()


class ApproveTaxonProposalTest(TestCase):
    def setUp(self):
        self.expert_user = User.objects.create_user('testuser', 'test@example.com', 'password')
        self.normal_user = User.objects.create_user('normal_user',
                                                    'normal_user@example.com', 'password')
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

        url = reverse('approve-taxon-proposal',
                      kwargs={
                          'taxonomy_update_proposal_id': taxonomy_update_proposal.pk,
                      })

        response = self.client.put(url, {}, content_type='application/json')

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
        self.child_taxon_group = TaxonGroupF.create(
            name='Test Group',
            parent=self.taxon_group,
            experts=(self.normal_user, )
        )
        taxonomy_update_proposal = TaxonomyUpdateProposalF.create(
            scientific_name='Updated Test Name',
            canonical_name='Updated Test Canonical Name',
            original_taxonomy=self.taxonomy,
            taxon_group=self.child_taxon_group
        )
        self.client.login(username='testuser', password='password')
        url = reverse('approve-taxon-proposal',
                      kwargs={
                          'taxonomy_update_proposal_id': taxonomy_update_proposal.pk,
                      })

        response = self.client.put(url, {}, content_type='application/json')

        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)

        updated_taxonomy = Taxonomy.objects.get(
            id=self.taxonomy.id
        )
        self.assertEqual(updated_taxonomy.scientific_name, 'Updated Test Name')
        self.assertEqual(updated_taxonomy.canonical_name, 'Updated Test Canonical Name')

        self.client.logout()
