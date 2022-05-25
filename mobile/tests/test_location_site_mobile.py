from django.contrib.gis.geos import Point
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from bims.tests.model_factories import LocationSiteF


class TestCeleryStatus(TestCase):

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
