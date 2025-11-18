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
from bims.models import TaxonGroupTaxonomy

User = get_user_model()


class UpdateTaxonTest(FastTenantTestCase):
    def setUp(self):
        self.client = TenantClient(self.tenant)
        self.expert_user = User.objects.create_user('testuser', 'test@example.com', 'password')
        self.normal_user = User.objects.create_user('normal_user',
                                                    'normal_user@example.com',
                                                    'password')
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
        self.client.login(username='normal_user', password='password')

        url = reverse('update-taxon',
                      kwargs={
                          'taxon_id': self.taxonomy.pk,
                          'taxon_group_id': self.taxon_group.pk
                      })

        response = self.client.put(url, {}, content_type='application/json')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.client.logout()

    def test_update_synonym_adds_accepted_name_to_group(self):
        """
        When updating a taxon to change it to a synonym,
        the accepted taxonomy should automatically be added to the group.
        """
        self.client.login(username='testuser', password='password')

        # Create an accepted taxonomy not yet in the group
        accepted_taxonomy = TaxonomyF.create(
            canonical_name='Accepted Name',
            scientific_name='Accepted Name',
            rank='species',
            taxonomic_status='ACCEPTED'
        )

        # Verify the accepted taxonomy is NOT in the group
        self.assertFalse(
            TaxonGroupTaxonomy.objects.filter(
                taxonomy=accepted_taxonomy,
                taxongroup=self.taxon_group
            ).exists()
        )

        # Update the taxonomy to make it a synonym
        url = reverse('update-taxon',
                      kwargs={
                          'taxon_id': self.taxonomy.pk,
                          'taxon_group_id': self.taxon_group.pk
                      })

        data = {
            'taxonomic_status': 'SYNONYM',
            'accepted_taxonomy': accepted_taxonomy.pk,
        }

        response = self.client.put(url, data, content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)

        # Verify the accepted taxonomy was automatically added to the group
        self.assertTrue(
            TaxonGroupTaxonomy.objects.filter(
                taxonomy=accepted_taxonomy,
                taxongroup=self.taxon_group
            ).exists(),
            "Accepted taxonomy should be automatically added when taxon becomes synonym"
        )

        self.client.logout()

    def test_create_proposal_for_synonym_adds_accepted_name(self):
        """
        Test that create_taxon_proposal automatically adds accepted taxonomy to group.
        """
        from bims.api_views.taxon_update import create_taxon_proposal

        # Create an accepted taxonomy
        accepted_taxonomy = TaxonomyF.create(
            canonical_name='Another Accepted',
            scientific_name='Another Accepted',
            rank='species',
            taxonomic_status='ACCEPTED'
        )

        # Create a new taxon that will be marked as synonym
        new_taxon = TaxonomyF.create(
            canonical_name='New Synonym',
            scientific_name='New Synonym',
            rank='species',
            taxonomic_status='SYNONYM',
            accepted_taxonomy=accepted_taxonomy
        )

        # Add to taxon group
        self.taxon_group.taxonomies.add(new_taxon)

        # Verify accepted not in group yet
        self.assertFalse(
            TaxonGroupTaxonomy.objects.filter(
                taxonomy=accepted_taxonomy,
                taxongroup=self.taxon_group
            ).exists()
        )

        # Create proposal
        proposal = create_taxon_proposal(
            taxon=new_taxon,
            taxon_group=self.taxon_group,
            data={'taxonomic_status': 'SYNONYM'},
            creator=self.expert_user
        )

        self.assertIsNotNone(proposal)

        # Verify accepted taxonomy was automatically added
        self.assertTrue(
            TaxonGroupTaxonomy.objects.filter(
                taxonomy=accepted_taxonomy,
                taxongroup=self.taxon_group
            ).exists(),
            "create_taxon_proposal should add accepted taxonomy to group"
        )
