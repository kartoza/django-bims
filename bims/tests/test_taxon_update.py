from django.urls import reverse
from django.test import TestCase
from django_tenants.test.cases import FastTenantTestCase
from django_tenants.test.client import TenantClient
from rest_framework import status
from django.contrib.auth import get_user_model
from bims.models.taxonomy_update_proposal import TaxonomyUpdateProposal
from bims.tests.model_factories import (
    TaxonomyF,
    TaxonGroupF,
    TaxonomyUpdateProposalF
)

User = get_user_model()


class UpdateTaxonTest(FastTenantTestCase):
    def setUp(self):
        self.client = TenantClient(self.tenant)
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

    def test_expert_propose_update_taxon(self):
        self.client.login(username='testuser', password='password')

        url = reverse('update-taxon',
                      kwargs={
                          'taxon_id': self.taxonomy.pk,
                          'taxon_group_id': self.taxon_group.pk
                      })

        data = {
            'scientific_name': 'Updated Test Name',
            'canonical_name': 'Updated Test Canonical Name',
        }

        response = self.client.put(url, data, content_type='application/json')

        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)

        self.assertTrue(TaxonomyUpdateProposal.objects.exists())

        proposal = TaxonomyUpdateProposal.objects.first()
        self.assertEqual(proposal.scientific_name, 'Updated Test Name')
        self.assertEqual(proposal.canonical_name, 'Updated Test Canonical Name')
        self.assertEqual(proposal.status, 'pending')
        self.assertEqual(proposal.original_taxonomy, self.taxonomy)

        self.client.logout()

    def test_non_expert_propose_taxon_update(self):
        self.client.login(username='normal_user', password='password')

        url = reverse('update-taxon',
                      kwargs={
                          'taxon_id': self.taxonomy.pk,
                          'taxon_group_id': self.taxon_group.pk
                      })

        response = self.client.put(url, {}, content_type='application/json')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.client.logout()

    def test_superuser_propose_taxon_update(self):
        self.client.login(username='superuser', password='password')

        url = reverse('update-taxon',
                      kwargs={
                          'taxon_id': self.taxonomy.pk,
                          'taxon_group_id': self.taxon_group.pk
                      })

        response = self.client.put(url, {}, content_type='application/json')

        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
        self.client.logout()

    def test_propose_taxon_update_in_pending(self):
        TaxonomyUpdateProposalF.create(
            original_taxonomy=self.taxonomy,
            taxon_group=self.taxon_group,
            status='pending'
        )
        self.client.login(username='superuser', password='password')

        url = reverse('update-taxon',
                      kwargs={
                          'taxon_id': self.taxonomy.pk,
                          'taxon_group_id': self.taxon_group.pk
                      })

        response = self.client.put(url, {}, content_type='application/json')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.client.logout()
