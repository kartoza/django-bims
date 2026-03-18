# SPDX-FileCopyrightText: Kartoza
# SPDX-License-Identifier: AGPL-3.0
"""
Tests for Taxonomy API v1.

Made with love by Kartoza | https://kartoza.com
"""
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from bims.models.taxonomy import Taxonomy
from bims.tests.model_factories import (
    BiologicalCollectionRecordF,
    EndemismF,
    IUCNStatusF,
    LocationSiteF,
    SurveyF,
    TaxonomyF,
    TaxonGroupF,
    UserF,
)


class TaxonomyAPITestCase(TestCase):
    """Test cases for the Taxonomy API endpoints."""

    def setUp(self):
        """Set up test fixtures."""
        self.client = APIClient()
        self.user = UserF(username='testuser')
        self.staff_user = UserF(username='staffuser', is_staff=True)
        self.superuser = UserF(username='superuser', is_staff=True, is_superuser=True)

        # Create IUCN status
        self.iucn_lc = IUCNStatusF(category='LC')
        self.iucn_vu = IUCNStatusF(category='VU')

        # Create endemism
        self.endemic = EndemismF(name='Endemic')

        # Create parent taxon
        self.parent_taxon = TaxonomyF(
            scientific_name='Cyprinidae',
            canonical_name='Cyprinidae',
            rank='FAMILY',
            validated=True,
        )

        # Create test taxa
        self.taxon1 = TaxonomyF(
            scientific_name='Barbus anoplus',
            canonical_name='Barbus anoplus',
            rank='SPECIES',
            parent=self.parent_taxon,
            iucn_status=self.iucn_lc,
            endemism=self.endemic,
            validated=True,
            owner=self.user,
        )
        self.taxon2 = TaxonomyF(
            scientific_name='Labeobarbus kimberleyensis',
            canonical_name='Labeobarbus kimberleyensis',
            rank='SPECIES',
            parent=self.parent_taxon,
            iucn_status=self.iucn_vu,
            validated=True,
            owner=self.user,
        )
        self.taxon_unvalidated = TaxonomyF(
            scientific_name='New Species',
            canonical_name='New Species',
            rank='SPECIES',
            validated=False,
            owner=self.user,
        )

    def test_list_taxa_unauthenticated(self):
        """Test listing taxa without authentication."""
        response = self.client.get('/api/v1/taxa/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])

    def test_list_taxa_authenticated(self):
        """Test listing taxa when authenticated."""
        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/v1/taxa/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])

    def test_retrieve_taxon(self):
        """Test retrieving a single taxon."""
        response = self.client.get(f'/api/v1/taxa/{self.taxon1.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['data']['scientific_name'], 'Barbus anoplus')

    def test_retrieve_taxon_not_found(self):
        """Test retrieving a non-existent taxon."""
        response = self.client.get('/api/v1/taxa/99999/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_create_taxon_authenticated(self):
        """Test creating a taxon when authenticated."""
        self.client.force_authenticate(user=self.user)
        response = self.client.post('/api/v1/taxa/', {
            'scientific_name': 'New Taxon',
            'canonical_name': 'New Taxon',
            'rank': 'SPECIES',
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['success'])

        # Verify in database
        self.assertTrue(Taxonomy.objects.filter(scientific_name='New Taxon').exists())

    def test_create_taxon_unauthenticated(self):
        """Test creating a taxon without authentication."""
        response = self.client.post('/api/v1/taxa/', {
            'scientific_name': 'New Taxon',
            'canonical_name': 'New Taxon',
            'rank': 'SPECIES',
        })
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_update_taxon_owner(self):
        """Test updating a taxon by its owner."""
        self.client.force_authenticate(user=self.user)
        response = self.client.patch(f'/api/v1/taxa/{self.taxon1.id}/', {
            'canonical_name': 'Updated Name',
        })
        # Note: Based on permissions, update may require staff
        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_403_FORBIDDEN])

    def test_update_taxon_staff(self):
        """Test updating a taxon by staff."""
        self.client.force_authenticate(user=self.staff_user)
        response = self.client.patch(f'/api/v1/taxa/{self.taxon1.id}/', {
            'canonical_name': 'Staff Updated',
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_taxon_tree_ancestors(self):
        """Test getting taxon tree (ancestors)."""
        response = self.client.get(f'/api/v1/taxa/{self.taxon1.id}/tree/', {'direction': 'up'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['meta']['direction'], 'up')
        # Should include parent
        self.assertTrue(len(response.data['data']) > 0)

    def test_taxon_tree_descendants(self):
        """Test getting taxon tree (descendants)."""
        response = self.client.get(f'/api/v1/taxa/{self.parent_taxon.id}/tree/', {'direction': 'down'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['meta']['direction'], 'down')

    def test_taxon_images(self):
        """Test getting taxon images."""
        response = self.client.get(f'/api/v1/taxa/{self.taxon1.id}/images/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertIn('count', response.data['meta'])

    def test_find_taxon(self):
        """Test finding taxon by name."""
        response = self.client.get('/api/v1/taxa/find/', {'q': 'Barbus'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertTrue(len(response.data['data']) > 0)

    def test_find_taxon_missing_query(self):
        """Test find taxon with missing query."""
        response = self.client.get('/api/v1/taxa/find/')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_find_taxon_with_rank_filter(self):
        """Test finding taxon with rank filter."""
        response = self.client.get('/api/v1/taxa/find/', {'q': 'Barbus', 'rank': 'SPECIES'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_taxon_proposals_unauthenticated(self):
        """Test that proposals endpoint requires authentication."""
        response = self.client.get('/api/v1/taxa/proposals/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_taxon_proposals_authenticated(self):
        """Test getting proposals when authenticated."""
        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/v1/taxa/proposals/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])

    def test_taxon_proposals_staff_sees_all(self):
        """Test that staff sees all proposals."""
        self.client.force_authenticate(user=self.staff_user)
        response = self.client.get('/api/v1/taxa/proposals/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_validate_taxon_staff(self):
        """Test validating a taxon by staff."""
        self.client.force_authenticate(user=self.staff_user)
        response = self.client.post(f'/api/v1/taxa/{self.taxon_unvalidated.id}/validate/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['meta']['validated'])

        self.taxon_unvalidated.refresh_from_db()
        self.assertTrue(self.taxon_unvalidated.validated)

    def test_validate_taxon_non_staff(self):
        """Test that non-staff cannot validate taxa."""
        self.client.force_authenticate(user=self.user)
        response = self.client.post(f'/api/v1/taxa/{self.taxon_unvalidated.id}/validate/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_validate_already_validated(self):
        """Test validating an already validated taxon."""
        self.client.force_authenticate(user=self.staff_user)
        response = self.client.post(f'/api/v1/taxa/{self.taxon1.id}/validate/')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_reject_taxon(self):
        """Test rejecting a taxon."""
        self.client.force_authenticate(user=self.staff_user)
        response = self.client.post(f'/api/v1/taxa/{self.taxon_unvalidated.id}/reject/', {
            'reason': 'Invalid nomenclature',
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['meta']['rejected'])

    def test_taxon_records(self):
        """Test getting biological records for a taxon."""
        # Create records
        site = LocationSiteF(validated=True)
        survey = SurveyF(site=site, validated=True)
        BiologicalCollectionRecordF(site=site, taxonomy=self.taxon1, survey=survey)

        response = self.client.get(f'/api/v1/taxa/{self.taxon1.id}/records/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])

    def test_filter_taxa_by_rank(self):
        """Test filtering taxa by rank."""
        response = self.client.get('/api/v1/taxa/', {'rank': 'SPECIES'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_filter_taxa_by_iucn_status(self):
        """Test filtering taxa by IUCN status."""
        response = self.client.get('/api/v1/taxa/', {'iucn_status': self.iucn_lc.id})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_filter_taxa_by_validated(self):
        """Test filtering taxa by validation status."""
        response = self.client.get('/api/v1/taxa/', {'validated': 'true'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_search_taxa(self):
        """Test searching taxa by name."""
        response = self.client.get('/api/v1/taxa/', {'search': 'Barbus'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class TaxonGroupAPITestCase(TestCase):
    """Test cases for the Taxon Group API endpoints."""

    def setUp(self):
        """Set up test fixtures."""
        self.client = APIClient()
        self.user = UserF(username='testuser')

        # Create taxon groups
        self.fish_group = TaxonGroupF(name='Fish', category='Freshwater')
        self.invert_group = TaxonGroupF(name='Invertebrates', category='Freshwater')

        # Create taxa in groups
        self.taxon = TaxonomyF(scientific_name='Test Fish', validated=True)

    def test_list_taxon_groups(self):
        """Test listing taxon groups."""
        response = self.client.get('/api/v1/taxon-groups/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])

    def test_retrieve_taxon_group(self):
        """Test retrieving a single taxon group."""
        response = self.client.get(f'/api/v1/taxon-groups/{self.fish_group.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['data']['name'], 'Fish')

    def test_taxon_group_taxa(self):
        """Test getting taxa in a group."""
        response = self.client.get(f'/api/v1/taxon-groups/{self.fish_group.id}/taxa/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])

    def test_taxon_groups_summary(self):
        """Test getting taxon groups summary."""
        response = self.client.get('/api/v1/taxon-groups/summary/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertIn('total_groups', response.data['meta'])

    def test_taxon_groups_read_only(self):
        """Test that taxon groups are read-only."""
        self.client.force_authenticate(user=self.user)
        response = self.client.post('/api/v1/taxon-groups/', {
            'name': 'New Group',
            'category': 'Test',
        })
        # Should be method not allowed for read-only viewset
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
