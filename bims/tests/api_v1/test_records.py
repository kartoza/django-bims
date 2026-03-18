# SPDX-FileCopyrightText: Kartoza
# SPDX-License-Identifier: AGPL-3.0
"""
Tests for Biological Collection Records API v1.

Made with love by Kartoza | https://kartoza.com
"""
from django.test import TestCase
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from bims.models.biological_collection_record import BiologicalCollectionRecord
from bims.tests.model_factories import (
    BiologicalCollectionRecordF,
    LocationSiteF,
    SurveyF,
    TaxonomyF,
    UserF,
)


class BiologicalRecordAPITestCase(TestCase):
    """Test cases for the Biological Collection Records API endpoints."""

    def setUp(self):
        """Set up test fixtures."""
        self.client = APIClient()
        self.user = UserF(username='testuser')
        self.staff_user = UserF(username='staffuser', is_staff=True)

        # Create base data
        self.site = LocationSiteF(name='Test Site', validated=True, owner=self.user)
        self.taxonomy = TaxonomyF(scientific_name='Test Species', validated=True)
        self.survey = SurveyF(site=self.site, validated=True, owner=self.user)

        # Create test records
        self.record1 = BiologicalCollectionRecordF(
            site=self.site,
            taxonomy=self.taxonomy,
            survey=self.survey,
            validated=True,
            owner=self.user,
            collection_date=timezone.now().date(),
        )
        self.record2 = BiologicalCollectionRecordF(
            site=self.site,
            taxonomy=self.taxonomy,
            survey=self.survey,
            validated=True,
            owner=self.user,
        )
        self.record_unvalidated = BiologicalCollectionRecordF(
            site=self.site,
            taxonomy=self.taxonomy,
            survey=self.survey,
            validated=False,
            owner=self.user,
        )

    def test_list_records_unauthenticated(self):
        """Test listing records without authentication."""
        response = self.client.get('/api/v1/records/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])

    def test_list_records_authenticated(self):
        """Test listing records when authenticated."""
        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/v1/records/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])

    def test_retrieve_record(self):
        """Test retrieving a single record."""
        response = self.client.get(f'/api/v1/records/{self.record1.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])

    def test_retrieve_record_not_found(self):
        """Test retrieving a non-existent record."""
        response = self.client.get('/api/v1/records/99999/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_create_record_authenticated(self):
        """Test creating a record when authenticated."""
        self.client.force_authenticate(user=self.user)
        response = self.client.post('/api/v1/records/', {
            'site': self.site.id,
            'taxonomy': self.taxonomy.id,
            'survey': self.survey.id,
            'collection_date': '2024-01-15',
            'original_species_name': 'Test Species',
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['success'])

    def test_create_record_unauthenticated(self):
        """Test creating a record without authentication."""
        response = self.client.post('/api/v1/records/', {
            'site': self.site.id,
            'taxonomy': self.taxonomy.id,
        })
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_update_record_owner(self):
        """Test updating a record by its owner."""
        self.client.force_authenticate(user=self.user)
        response = self.client.patch(f'/api/v1/records/{self.record1.id}/', {
            'notes': 'Updated notes',
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_update_record_non_owner(self):
        """Test updating a record by non-owner (should fail)."""
        other_user = UserF(username='otheruser')
        self.client.force_authenticate(user=other_user)
        response = self.client.patch(f'/api/v1/records/{self.record1.id}/', {
            'notes': 'Unauthorized update',
        })
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_record_owner(self):
        """Test deleting a record by owner."""
        self.client.force_authenticate(user=self.user)
        record_id = self.record1.id
        response = self.client.delete(f'/api/v1/records/{record_id}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(BiologicalCollectionRecord.objects.filter(id=record_id).exists())

    def test_records_summary(self):
        """Test records summary statistics endpoint."""
        response = self.client.get('/api/v1/records/summary/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertIn('total_records', response.data['data'])
        self.assertIn('validated_records', response.data['data'])
        self.assertIn('species_count', response.data['data'])
        self.assertIn('site_count', response.data['data'])

    def test_search_records(self):
        """Test searching records."""
        response = self.client.get('/api/v1/records/search/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])

    def test_search_records_group_by_taxon(self):
        """Test searching records grouped by taxon."""
        response = self.client.get('/api/v1/records/search/', {'group_by': 'taxon'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['meta']['grouped_by'], 'taxon')

    def test_search_records_group_by_site(self):
        """Test searching records grouped by site."""
        response = self.client.get('/api/v1/records/search/', {'group_by': 'site'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['meta']['grouped_by'], 'site')

    def test_search_records_group_by_year(self):
        """Test searching records grouped by year."""
        response = self.client.get('/api/v1/records/search/', {'group_by': 'year'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['meta']['grouped_by'], 'year')

    def test_validate_record_staff(self):
        """Test validating a record by staff."""
        self.client.force_authenticate(user=self.staff_user)
        response = self.client.post(f'/api/v1/records/{self.record_unvalidated.id}/validate/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['meta']['validated'])

        self.record_unvalidated.refresh_from_db()
        self.assertTrue(self.record_unvalidated.validated)

    def test_validate_record_non_staff(self):
        """Test that non-staff cannot validate records."""
        self.client.force_authenticate(user=self.user)
        response = self.client.post(f'/api/v1/records/{self.record_unvalidated.id}/validate/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_reject_record(self):
        """Test rejecting a record."""
        self.client.force_authenticate(user=self.staff_user)
        response = self.client.post(f'/api/v1/records/{self.record_unvalidated.id}/reject/', {
            'reason': 'Invalid identification',
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['meta']['rejected'])

    def test_records_by_site(self):
        """Test getting records grouped by site."""
        response = self.client.get('/api/v1/records/by_site/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertIn('total_sites', response.data['meta'])

    def test_records_by_site_filtered(self):
        """Test getting records for a specific site."""
        response = self.client.get('/api/v1/records/by_site/', {'site_id': self.site.id})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])

    def test_records_by_taxon(self):
        """Test getting records grouped by taxon."""
        response = self.client.get('/api/v1/records/by_taxon/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertIn('total_taxa', response.data['meta'])

    def test_filter_records_by_validated(self):
        """Test filtering records by validation status."""
        response = self.client.get('/api/v1/records/', {'validated': 'true'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_filter_records_by_site(self):
        """Test filtering records by site."""
        response = self.client.get('/api/v1/records/', {'site': self.site.id})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_filter_records_by_taxonomy(self):
        """Test filtering records by taxonomy."""
        response = self.client.get('/api/v1/records/', {'taxonomy': self.taxonomy.id})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
