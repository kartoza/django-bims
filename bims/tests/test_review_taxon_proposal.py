from django.urls import reverse
from django_tenants.test.cases import FastTenantTestCase
from django_tenants.test.client import TenantClient
from rest_framework import status
from django.contrib.auth import get_user_model

from bims.api_views.taxon_group import add_taxa_to_taxon_group
from bims.models import TaxonGroupTaxonomy
from bims.models.taxonomy_update_proposal import (
    TaxonomyUpdateProposal,
    TaxonomyUpdateReviewer
)
from bims.models.taxonomy import Taxonomy
from bims.tests.model_factories import (
    TaxonomyF,
    TaxonGroupF,
    TaxonomyUpdateProposalF,
    IUCNStatusF
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
            name='Test Group 1',
            taxonomies=(self.taxonomy,),
            experts=(self.expert_user,)
        )
        self.parent = TaxonomyF.create()
        self.family = TaxonomyF.create(
            rank='FAMILY',
            parent=self.parent
        )
        self.iucn_status = IUCNStatusF.create()

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

    def test_expert_approve_taxon(self):
        self.client.login(
            username='normal_user',
            password='password')
        experts_2 = User.objects.create_user(
            'experts_2',
            'experts_2@example.com', 'password')
        experts_3 = User.objects.create_user(
            'experts_3',
            'experts_3@example.com', 'password')

        taxon_group_level_2 = TaxonGroupF.create(
            name='taxon group 2',
            parent=self.taxon_group,
            experts=(experts_2,))
        taxon_group_level_3 = TaxonGroupF.create(
            name='taxon group 3',
            parent=taxon_group_level_2,
            experts=(experts_3,))

        # Call add-new-taxon api
        url = reverse('add-new-taxon')
        data = {
            'taxonName': 'New Taxon1',
            'rank': 'species',
            'familyId': self.family.id,
            'taxonGroup': taxon_group_level_3,
            'taxonGroupId': taxon_group_level_3.id
        }
        response = self.client.post(url, data)

        self.assertEqual(response.status_code, 200)

        # Check taxa is still unvalidated, and new proposal has been created
        proposal = TaxonomyUpdateProposal.objects.filter(
            canonical_name='New Taxon1'
        ).first()
        taxon = Taxonomy.objects.filter(
            canonical_name='New Taxon1'
        ).first()
        self.assertIsNotNone(
            taxon
        )
        self.assertIsNotNone(
            proposal
        )

        # Check if the can_be_validated flag appears for the expert of taxon group level 3.
        self.client.login(username='experts_3', password='password')
        taxa_list_url = reverse('taxa-list')
        unvalidated_taxa_list_url = f'{taxa_list_url}?taxonGroup={taxon_group_level_3.id}&validated=False'
        response = self.client.get(unvalidated_taxa_list_url)
        self.assertEqual(
            response.data['results'][0]['scientific_name'],
            'New Taxon1'
        )
        self.assertTrue(
            response.data['results'][0]['can_be_validated']
        )
        self.assertTrue(
            TaxonGroupTaxonomy.objects.filter(
                taxonomy=taxon,
                taxongroup=taxon_group_level_3,
                is_validated=False
            )
        )
        self.assertEqual(
            TaxonomyUpdateProposal.objects.get(
                id=proposal.id
            ).taxon_group_under_review,
            taxon_group_level_3
        )

        # The expert of taxon group level 3 validates the taxa.
        review_taxon_url = reverse(
            'review-taxon',
            kwargs={
               'taxon_id': taxon.id,
               'taxon_group_id': taxon_group_level_3.id
            })
        response = self.client.put(
            review_taxon_url, {
                'action': 'approve'
            },
            content_type='application/json')
        self.assertEqual(
            response.status_code,
            status.HTTP_202_ACCEPTED
        )

        # Check if the expert of taxon group level 3 is added to the reviewer list.
        self.assertEqual(
            TaxonomyUpdateReviewer.objects.filter(
                reviewer=experts_3,
                taxonomy_update_proposal=proposal,
            ).first().status,
            'approved'
        )
        updated_proposal = (
            TaxonomyUpdateProposal.objects.filter(
                id=proposal.id
            ).first()
        )
        self.assertEqual(
            updated_proposal.status,
            'pending'
        )

        # Check if the proposal updates the taxon_group_under_review
        # to the highest parent.
        self.assertEqual(
            updated_proposal.taxon_group_under_review,
            self.taxon_group
        )

        # Check if the can_be_validated flag appears for the expert of taxon group level 1
        # but not for the expert of taxon group level 2 or 3.
        self.client.login(username='experts_2', password='password')
        taxa_list_url = reverse('taxa-list')
        unvalidated_taxa_list_url = f'{taxa_list_url}?taxonGroup={taxon_group_level_2.id}&validated=False'
        response = self.client.get(unvalidated_taxa_list_url)
        self.assertEqual(
            response.data['results'][0]['scientific_name'],
            'New Taxon1'
        )
        self.assertFalse(
            response.data['results'][0]['can_be_validated']
        )

        # - can_be_validated should not appear in the taxon group level 3 anymore
        taxa_list_url = reverse('taxa-list')
        unvalidated_taxa_list_url = f'{taxa_list_url}?taxonGroup={taxon_group_level_3.id}&validated=False'
        response = self.client.get(unvalidated_taxa_list_url)
        self.assertFalse(
            response.data['results'][0]['can_be_validated']
        )

        # The expert of taxon group level 2 validates the taxa.
        self.client.login(username='experts_2', password='password')
        response = self.client.put(
            review_taxon_url, {
                'action': 'approve'
            },
            content_type='application/json')
        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN
        )

        # Check if the can_be_validated flag appears for the expert of taxon group level 1
        # but not for other levels.
        self.client.login(
            username='testuser',
            password='password'
        )
        taxa_list_url = reverse('taxa-list')
        unvalidated_taxa_list_url = f'{taxa_list_url}?taxonGroup={self.taxon_group.id}&validated=False'
        response = self.client.get(unvalidated_taxa_list_url)
        self.assertEqual(
            response.data['results'][0]['scientific_name'],
            'New Taxon1'
        )
        self.assertTrue(
            response.data['results'][0]['can_be_validated']
        )
        self.client.login(username='experts_2', password='password')
        unvalidated_taxa_list_url = f'{taxa_list_url}?taxonGroup={self.taxon_group.id}&validated=False'
        response = self.client.get(unvalidated_taxa_list_url)
        self.assertFalse(
            response.data['results'][0]['can_be_validated']
        )

        # The expert of taxon group level 1 validates the taxa.
        self.client.login(
            username='testuser',
            password='password'
        )
        response = self.client.put(
            review_taxon_url, {
                'action': 'approve'
            },
            content_type='application/json')
        self.assertEqual(
            response.status_code,
            status.HTTP_202_ACCEPTED
        )

        # Check if the expert of taxon group level 1 is added to the reviewer list.
        self.assertEqual(
            TaxonomyUpdateReviewer.objects.filter(
                reviewer=self.expert_user,
                taxonomy_update_proposal=proposal,
            ).first().status,
            'approved'
        )

        # Check if the taxa is validated.
        self.assertTrue(
            TaxonGroupTaxonomy.objects.filter(
                taxonomy=taxon,
                taxongroup=taxon_group_level_3
            ).first().is_validated
        )

        # Check if the proposal is updated to approved.
        updated_proposal = (
            TaxonomyUpdateProposal.objects.filter(
                id=proposal.id
            ).first()
        )
        self.assertEqual(
            updated_proposal.status,
            'approved'
        )

    def test_parent_expert_approve_update_taxon(self):
        self.taxon_group_level_2 = TaxonGroupF.create(
            name='Test Group',
            parent=self.taxon_group,
            experts=(self.normal_user,)
        )
        self.taxon_group_level_3 = TaxonGroupF.create(
            name='Test Group',
            parent=self.taxon_group_level_2,
            experts=(self.user_2,)
        )
        taxonomy_update_proposal = TaxonomyUpdateProposalF.create(
            scientific_name='Updated Test Name',
            canonical_name='Updated Test Canonical Name',
            original_taxonomy=self.taxonomy,
            taxon_group=self.taxon_group_level_3,
            taxon_group_under_review=self.taxon_group_level_3
        )
        self.client.login(username='user_2', password='password')
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
        self.assertNotEqual(
            updated_taxonomy.scientific_name,
            'Updated Test Name')
        self.assertNotEqual(
            updated_taxonomy.canonical_name,
            'Updated Test Canonical Name')

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
            taxon_group=self.taxon_group,
            taxon_group_under_review=self.taxon_group
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

    def test_reject_new_taxon(self):
        new_taxon_group = TaxonGroupF.create(
            experts=(self.expert_user,)
        )
        add_taxa_to_taxon_group([
            self.taxonomy.id
        ], new_taxon_group.id)
        taxonomy_update_proposal = TaxonomyUpdateProposal.objects.filter(
            original_taxonomy=self.taxonomy,
            taxon_group=new_taxon_group,
            status='pending',
        ).first()
        self.assertTrue(taxonomy_update_proposal.new_data)
        self.client.login(username='testuser', password='password')
        url = reverse('review-taxon-proposal',
                      kwargs={
                          'taxonomy_update_proposal_id':
                              taxonomy_update_proposal.pk
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
        self.assertFalse(
            TaxonGroupTaxonomy.objects.filter(
                taxongroup=self.taxon_group,
                taxonomy=self.taxonomy,
                is_validated=True
            ).exists()
        )
        self.client.logout()

    def test_superuser_update_taxon(self):
        self.client.login(username='superuser', password='password')

        url = reverse('edit_taxon', kwargs={
            'id': self.taxonomy.id,
            'taxon_group_id': self.taxon_group.id
        })

        data = {
            'canonical_name': 'Updated Taxon',
            'rank': 'SPECIES',
            'author': 'Updated Author',
            'iucn_status': self.iucn_status.id,
            'taxonomic_status': 'ACCEPTED',
            'accepted_taxonomy': '',
            'tags': [],
            'parent': self.parent.id,
        }

        response = self.client.post(url, data)

        # Refresh the taxon from the database
        self.taxonomy.refresh_from_db()

        # Verify the taxon was updated
        self.assertEqual(self.taxonomy.canonical_name, 'Updated Taxon')

        # Verify that the proposal was created and approved
        proposal = TaxonomyUpdateProposal.objects.get(original_taxonomy=self.taxonomy)
        self.assertIsNotNone(proposal)
        self.assertEqual(proposal.status, 'approved')
