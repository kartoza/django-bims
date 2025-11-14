from django.urls import reverse
from django.test import override_settings
from django_tenants.test.cases import FastTenantTestCase
from django_tenants.test.client import TenantClient
from django.contrib.auth import get_user_model
from preferences import preferences

from bims.models.taxonomy_update_proposal import TaxonomyUpdateProposal
from bims.models.taxonomy import Taxonomy
from bims.tests.model_factories import (
    TaxonomyF,
    TaxonGroupF,
    IUCNStatusF
)

User = get_user_model()


class EditTaxonFadaTest(FastTenantTestCase):
    """Test cases for FADA_ID field in edit taxon functionality."""

    def setUp(self):
        self.client = TenantClient(self.tenant)
        self.superuser = User.objects.create_user(
            username='superuser',
            email='superuser@example.com',
            password='password',
            is_superuser=True
        )
        self.expert_user = User.objects.create_user(
            'expert',
            'expert@example.com',
            'password'
        )
        self.parent = TaxonomyF.create(
            rank='GENUS',
            canonical_name='TestGenus'
        )
        self.taxonomy = TaxonomyF.create(
            scientific_name='Test Name',
            canonical_name='Test Canonical Name',
            parent=self.parent,
            rank='SPECIES'
        )
        self.taxon_group = TaxonGroupF.create(
            name='Test Group',
            taxonomies=(self.taxonomy,),
            experts=(self.expert_user,)
        )
        self.iucn_status = IUCNStatusF.create()

    def test_fada_id_field_saved_in_proposal(self):
        """Test that FADA_ID is properly saved when editing a taxon."""
        self.client.login(username='superuser', password='password')

        url = reverse('edit_taxon', kwargs={
            'id': self.taxonomy.id,
            'taxon_group_id': self.taxon_group.id
        })

        fada_id_value = 'FADA123456'

        data = {
            'taxon_name': 'Updated Taxon',
            'rank': 'SPECIES',
            'author': 'Test Author',
            'iucn_status': self.iucn_status.id,
            'taxonomic_status': 'ACCEPTED',
            'accepted_taxonomy': '',
            'tags': [],
            'parent': self.parent.id,
            'fada_id': fada_id_value,
        }

        response = self.client.post(url, data)

        # Check that redirect occurred (success)
        self.assertEqual(response.status_code, 302)

        # Verify that a proposal was created with the FADA_ID
        proposal = TaxonomyUpdateProposal.objects.filter(
            original_taxonomy=self.taxonomy,
            taxon_group=self.taxon_group,
            status='pending'
        ).first()

        self.assertIsNotNone(proposal)
        self.assertEqual(proposal.fada_id, fada_id_value)

        self.client.logout()

    def test_fada_id_field_updated_in_existing_proposal(self):
        """Test that FADA_ID is updated in an existing proposal."""
        self.client.login(username='expert', password='password')

        url = reverse('edit_taxon', kwargs={
            'id': self.taxonomy.id,
            'taxon_group_id': self.taxon_group.id
        })

        # Create initial proposal
        initial_fada_id = 'FADA000001'
        data = {
            'taxon_name': 'Updated Taxon',
            'rank': 'SPECIES',
            'author': 'Test Author',
            'iucn_status': self.iucn_status.id,
            'taxonomic_status': 'ACCEPTED',
            'accepted_taxonomy': '',
            'tags': [],
            'parent': self.parent.id,
            'fada_id': initial_fada_id,
        }

        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)

        # Verify initial FADA_ID
        proposal = TaxonomyUpdateProposal.objects.filter(
            original_taxonomy=self.taxonomy,
            taxon_group=self.taxon_group,
            status='pending'
        ).first()
        self.assertEqual(proposal.fada_id, initial_fada_id)

        # Update with new FADA_ID
        updated_fada_id = 'FADA999999'
        data['fada_id'] = updated_fada_id

        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)

        # Verify updated FADA_ID
        proposal.refresh_from_db()
        self.assertEqual(proposal.fada_id, updated_fada_id)

        self.client.logout()

    def test_fada_id_empty_string_becomes_none(self):
        """Test that empty FADA_ID string is converted to None."""
        self.client.login(username='superuser', password='password')

        url = reverse('edit_taxon', kwargs={
            'id': self.taxonomy.id,
            'taxon_group_id': self.taxon_group.id
        })

        data = {
            'taxon_name': 'Updated Taxon',
            'rank': 'SPECIES',
            'author': 'Test Author',
            'iucn_status': self.iucn_status.id,
            'taxonomic_status': 'ACCEPTED',
            'accepted_taxonomy': '',
            'tags': [],
            'parent': self.parent.id,
            'fada_id': '',  # Empty string
        }

        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)

        # Verify that FADA_ID is None (not empty string)
        proposal = TaxonomyUpdateProposal.objects.filter(
            original_taxonomy=self.taxonomy,
            taxon_group=self.taxon_group,
            status='pending'
        ).first()

        self.assertIsNotNone(proposal)
        self.assertIsNone(proposal.fada_id)

        self.client.logout()

    def test_fada_id_whitespace_stripped(self):
        """Test that whitespace is stripped from FADA_ID."""
        self.client.login(username='superuser', password='password')

        url = reverse('edit_taxon', kwargs={
            'id': self.taxonomy.id,
            'taxon_group_id': self.taxon_group.id
        })

        data = {
            'taxon_name': 'Updated Taxon',
            'rank': 'SPECIES',
            'author': 'Test Author',
            'iucn_status': self.iucn_status.id,
            'taxonomic_status': 'ACCEPTED',
            'accepted_taxonomy': '',
            'tags': [],
            'parent': self.parent.id,
            'fada_id': '  FADA123  ',  # With whitespace
        }

        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)

        # Verify that FADA_ID has whitespace stripped
        proposal = TaxonomyUpdateProposal.objects.filter(
            original_taxonomy=self.taxonomy,
            taxon_group=self.taxon_group,
            status='pending'
        ).first()

        self.assertIsNotNone(proposal)
        self.assertEqual(proposal.fada_id, 'FADA123')

        self.client.logout()

    def test_fada_id_in_proposal(self):
        """Test that FADA_ID is stored in the proposal correctly."""
        self.client.login(username='expert', password='password')

        url = reverse('edit_taxon', kwargs={
            'id': self.taxonomy.id,
            'taxon_group_id': self.taxon_group.id
        })

        fada_id_value = 'FADA_IN_PROPOSAL'

        data = {
            'taxon_name': 'TestGenus InProposal',
            'rank': 'SPECIES',
            'author': 'Test Author',
            'iucn_status': self.iucn_status.id,
            'taxonomic_status': 'ACCEPTED',
            'accepted_taxonomy': '',
            'tags': [],
            'parent': self.parent.id,
            'fada_id': fada_id_value,
        }

        # Create proposal with FADA_ID
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)

        proposal = TaxonomyUpdateProposal.objects.filter(
            original_taxonomy=self.taxonomy,
            taxon_group=self.taxon_group,
            status='pending'
        ).first()

        self.assertIsNotNone(proposal)
        self.assertEqual(proposal.fada_id, fada_id_value)
        # Verify the proposal has all necessary fields
        self.assertEqual(proposal.status, 'pending')
        self.assertEqual(proposal.original_taxonomy, self.taxonomy)

        self.client.logout()

    def test_fada_id_not_required(self):
        """Test that FADA_ID is optional and form works without it."""
        self.client.login(username='superuser', password='password')

        url = reverse('edit_taxon', kwargs={
            'id': self.taxonomy.id,
            'taxon_group_id': self.taxon_group.id
        })

        # Don't include fada_id in data
        data = {
            'taxon_name': 'Updated Taxon',
            'rank': 'SPECIES',
            'author': 'Test Author',
            'iucn_status': self.iucn_status.id,
            'taxonomic_status': 'ACCEPTED',
            'accepted_taxonomy': '',
            'tags': [],
            'parent': self.parent.id,
        }

        response = self.client.post(url, data)

        # Should still succeed
        self.assertEqual(response.status_code, 302)

        # Verify proposal was created
        proposal = TaxonomyUpdateProposal.objects.filter(
            original_taxonomy=self.taxonomy,
            taxon_group=self.taxon_group,
            status='pending'
        ).first()

        self.assertIsNotNone(proposal)
        # FADA_ID should be None
        self.assertIsNone(proposal.fada_id)

        self.client.logout()
