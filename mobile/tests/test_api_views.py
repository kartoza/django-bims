from django.contrib.gis.geos import Point
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from bims.tests.model_factories import (
    LocationSiteF, TaxonomyF,
    TaxonGroupF, UserF, BiotopeF
)


class TestLocationSiteMobile(TestCase):

    def test_get_nearest_location_sites_without_coord(self):
        api_url = (
            reverse('mobile-nearest-sites')
        )
        client = APIClient()
        res = client.get(api_url)
        self.assertEqual(
            res.status_code, status.HTTP_404_NOT_FOUND
        )

    def test_get_nearest_location_sites(self):
        LocationSiteF.create(
            geometry_point=Point(
                -31,
                30
            )
        )

        api_url = (
                reverse('mobile-nearest-sites') +
                '?lat=30.001&lon=-31.001'
        )
        client = APIClient()
        res = client.get(api_url)
        self.assertEqual(
            res.status_code, status.HTTP_200_OK
        )
        self.assertTrue(len(res.data) > 0)


class TestAllTaxaAPI(TestCase):
    def test_get_all_taxa_without_module(self):
        api_url = (
            reverse('all-taxa')
        )
        client = APIClient()
        user = UserF.create(is_superuser=True)
        client.login(
            username=user.username,
            password='password'
        )
        res = client.get(api_url)
        self.assertEqual(
            res.status_code,
            status.HTTP_404_NOT_FOUND)

    def test_get_all_taxa(self):
        taxon = TaxonomyF.create(
            rank='SPECIES'
        )
        taxon_group = TaxonGroupF.create(
            taxonomies=(taxon,)
        )

        api_url = (
                reverse('all-taxa') +
                f'?module={taxon_group.id}'
        )
        client = APIClient()
        user = UserF.create(is_superuser=True)
        client.login(
            username=user.username,
            password='password'
        )
        res = client.get(api_url)
        self.assertEqual(
            res.status_code, status.HTTP_200_OK
        )
        self.assertEqual(
            taxon.id,
            res.data[0].get('id')
        )


class TestChoicesApi(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        user = UserF.create(is_superuser=True)
        self.client.login(
            username=user.username,
            password='password'
        )
        self.api_url = reverse('all-choices')

    def test_get_all_choices_without_module(self):
        res = self.client.get(self.api_url)
        self.assertEqual(
            res.status_code, status.HTTP_404_NOT_FOUND
        )

    def test_get_all_choices(self):
        taxon_group = TaxonGroupF.create()
        biotope = BiotopeF.create(
            biotope_type='broad',
            taxon_group=(taxon_group,)
        )
        res = self.client.get(
            self.api_url + f'?module={taxon_group.id}'
        )
        self.assertEqual(
            res.status_code, status.HTTP_200_OK
        )
        self.assertEqual(
            res.data.get('broad_biotope')[0]['id'],
            biotope.id
        )
