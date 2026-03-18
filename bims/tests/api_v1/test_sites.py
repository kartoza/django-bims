# SPDX-FileCopyrightText: Kartoza
# SPDX-License-Identifier: AGPL-3.0
"""
Tests for Location Sites API v1.

Made with love by Kartoza | https://kartoza.com
"""
from django.contrib.gis.geos import Point
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from bims.models.location_site import LocationSite
from bims.tests.model_factories import (
    BiologicalCollectionRecordF,
    LocationSiteF,
    LocationTypeF,
    SurveyF,
    TaxonomyF,
    UserF,
)


class LocationSiteAPITestCase(TestCase):
    """Test cases for the Location Sites API endpoints."""

    def setUp(self):
        """Set up test fixtures."""
        self.client = APIClient()
        self.user = UserF(username='testuser')
        self.staff_user = UserF(username='staffuser', is_staff=True)
        self.superuser = UserF(username='superuser', is_staff=True, is_superuser=True)

        # Create location type
        self.location_type = LocationTypeF(name='River')

        # Create test sites
        self.site1 = LocationSiteF(
            name='Site 1',
            site_code='SITE001',
            latitude=-28.5,
            longitude=24.5,
            geometry_point=Point(24.5, -28.5, srid=4326),
            location_type=self.location_type,
            validated=True,
            owner=self.user,
        )
        self.site2 = LocationSiteF(
            name='Site 2',
            site_code='SITE002',
            latitude=-29.5,
            longitude=25.5,
            geometry_point=Point(25.5, -29.5, srid=4326),
            location_type=self.location_type,
            validated=True,
            owner=self.user,
        )
        self.site_unvalidated = LocationSiteF(
            name='Unvalidated Site',
            site_code='UNVAL001',
            latitude=-30.5,
            longitude=26.5,
            geometry_point=Point(26.5, -30.5, srid=4326),
            location_type=self.location_type,
            validated=False,
            owner=self.user,
        )

    def test_list_sites_unauthenticated(self):
        """Test listing sites without authentication."""
        response = self.client.get('/api/v1/sites/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertIsInstance(response.data['data'], list)

    def test_list_sites_authenticated(self):
        """Test listing sites when authenticated."""
        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/v1/sites/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])

    def test_retrieve_site(self):
        """Test retrieving a single site."""
        response = self.client.get(f'/api/v1/sites/{self.site1.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['data']['name'], 'Site 1')
        self.assertEqual(response.data['data']['site_code'], 'SITE001')

    def test_retrieve_site_not_found(self):
        """Test retrieving a non-existent site."""
        response = self.client.get('/api/v1/sites/99999/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_create_site_authenticated(self):
        """Test creating a site when authenticated."""
        self.client.force_authenticate(user=self.user)
        response = self.client.post('/api/v1/sites/', {
            'name': 'New Site',
            'site_code': 'NEW001',
            'latitude': -31.5,
            'longitude': 27.5,
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['data']['name'], 'New Site')

        # Verify in database
        self.assertTrue(LocationSite.objects.filter(site_code='NEW001').exists())

    def test_create_site_unauthenticated(self):
        """Test creating a site without authentication."""
        response = self.client.post('/api/v1/sites/', {
            'name': 'New Site',
            'site_code': 'NEW002',
            'latitude': -31.5,
            'longitude': 27.5,
        })
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_update_site_owner(self):
        """Test updating a site by its owner."""
        self.client.force_authenticate(user=self.user)
        response = self.client.patch(f'/api/v1/sites/{self.site1.id}/', {
            'name': 'Updated Site Name',
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.site1.refresh_from_db()
        self.assertEqual(self.site1.name, 'Updated Site Name')

    def test_update_site_non_owner(self):
        """Test updating a site by non-owner (should fail)."""
        other_user = UserF(username='otheruser')
        self.client.force_authenticate(user=other_user)
        response = self.client.patch(f'/api/v1/sites/{self.site1.id}/', {
            'name': 'Unauthorized Update',
        })
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_site_staff(self):
        """Test that staff can update any site."""
        self.client.force_authenticate(user=self.staff_user)
        response = self.client.patch(f'/api/v1/sites/{self.site1.id}/', {
            'name': 'Staff Updated',
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_delete_site_owner(self):
        """Test deleting a site by owner."""
        self.client.force_authenticate(user=self.user)
        site_id = self.site1.id
        response = self.client.delete(f'/api/v1/sites/{site_id}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(LocationSite.objects.filter(id=site_id).exists())

    def test_delete_site_non_owner(self):
        """Test deleting a site by non-owner (should fail)."""
        other_user = UserF(username='deleteuser')
        self.client.force_authenticate(user=other_user)
        response = self.client.delete(f'/api/v1/sites/{self.site1.id}/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_site_summary(self):
        """Test site summary statistics endpoint."""
        response = self.client.get('/api/v1/sites/summary/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertIn('total_sites', response.data['data'])
        self.assertIn('validated_sites', response.data['data'])
        self.assertIn('pending_sites', response.data['data'])

    def test_nearby_sites(self):
        """Test finding nearby sites."""
        response = self.client.get('/api/v1/sites/nearby/', {
            'lat': -28.5,
            'lon': 24.5,
            'radius': 100000,  # 100km
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertIsInstance(response.data['data'], list)

    def test_nearby_sites_missing_params(self):
        """Test nearby sites with missing parameters."""
        response = self.client.get('/api/v1/sites/nearby/')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_coordinates_lookup(self):
        """Test finding site by coordinates."""
        response = self.client.get('/api/v1/sites/coordinates/', {
            'lat': -28.5,
            'lon': 24.5,
            'tolerance': 0.001,
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])

    def test_coordinates_lookup_not_found(self):
        """Test coordinates lookup with no match."""
        response = self.client.get('/api/v1/sites/coordinates/', {
            'lat': 0.0,
            'lon': 0.0,
            'tolerance': 0.001,
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data['meta']['found'])

    def test_validate_site_staff(self):
        """Test validating a site by staff."""
        self.client.force_authenticate(user=self.staff_user)
        response = self.client.post(f'/api/v1/sites/{self.site_unvalidated.id}/validate/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['meta']['validated'])

        self.site_unvalidated.refresh_from_db()
        self.assertTrue(self.site_unvalidated.validated)

    def test_validate_site_non_staff(self):
        """Test that non-staff cannot validate sites."""
        self.client.force_authenticate(user=self.user)
        response = self.client.post(f'/api/v1/sites/{self.site_unvalidated.id}/validate/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_validate_already_validated(self):
        """Test validating an already validated site."""
        self.client.force_authenticate(user=self.staff_user)
        response = self.client.post(f'/api/v1/sites/{self.site1.id}/validate/')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_reject_site(self):
        """Test rejecting a site."""
        self.client.force_authenticate(user=self.staff_user)
        response = self.client.post(f'/api/v1/sites/{self.site_unvalidated.id}/reject/', {
            'reason': 'Invalid coordinates',
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['meta']['rejected'])

    def test_site_surveys(self):
        """Test getting surveys for a site."""
        # Create a survey
        SurveyF(site=self.site1)

        response = self.client.get(f'/api/v1/sites/{self.site1.id}/surveys/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertIsInstance(response.data['data'], list)

    def test_site_records(self):
        """Test getting biological records for a site."""
        # Create records
        taxonomy = TaxonomyF()
        survey = SurveyF(site=self.site1)
        BiologicalCollectionRecordF(site=self.site1, taxonomy=taxonomy, survey=survey)

        response = self.client.get(f'/api/v1/sites/{self.site1.id}/records/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])

    def test_filter_sites_by_validated(self):
        """Test filtering sites by validation status."""
        response = self.client.get('/api/v1/sites/', {'validated': 'true'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # All returned sites should be validated
        for site in response.data['data']:
            self.assertTrue(site.get('validated', True))

    def test_search_sites(self):
        """Test searching sites by name/code."""
        response = self.client.get('/api/v1/sites/', {'search': 'Site 1'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
