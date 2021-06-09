from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from bims.tests.model_factories import LocationSiteF, UserF


class TestRejectLocationSite(TestCase):

    def setUp(self):
        self.location_site = LocationSiteF.create()

    def test_reject_location_site(self):
        client = APIClient()
        api_url = '/api/reject-location-site/'
        site = LocationSiteF.create()

        # Cannot merge sites without log in as superuser
        res = client.get(api_url, {'pk': site.id})
        self.assertTrue(
            res.status_code == status.HTTP_403_FORBIDDEN
        )

        user = UserF.create(is_superuser=True)
        client.login(
            username=user.username,
            password='password'
        )

        res = client.get(api_url, {})

        self.assertTrue(
            res.status_code == status.HTTP_400_BAD_REQUEST
        )

        res = client.get(api_url, {
            'pk': site.id
        })
        self.assertTrue(
            res.status_code == status.HTTP_200_OK
        )
        self.assertEqual(site.rejected, True)








