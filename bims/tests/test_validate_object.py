import logging
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from bims.models import LocationSite
from bims.tests.model_factories import LocationSiteF, UserF

logger = logging.getLogger('bims')


class TestValidateLocationSite(TestCase):

    def setUp(self):
        self.location_site = LocationSiteF.create()

    def test_validate_location_site(self):
        client = APIClient()
        api_url = '/api/validate-location-site/'
        # Cannot merge sites without log in as superuser
        res = client.get(api_url, {})
        self.assertTrue(
            res.status_code == status.HTTP_302_FOUND
        )

        user = UserF.create(is_superuser=True)
        client.login(
            username=user.username,
            password='password'
        )

        res = client.get(api_url, {})
        self.assertTrue(
            res.status_code == status.HTTP_403_FORBIDDEN
        )

        site = LocationSiteF.create()
        res = client.get(api_url, {
            'pk': site.id
        })
        self.assertTrue(
            res.status_code == status.HTTP_200_OK
        )
        site = LocationSite.objects.get(pk=site.id)
        self.assertEqual(site.validated, True)








