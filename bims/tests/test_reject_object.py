from django.db.models import signals
from django.test import TestCase
import mock
from django_tenants.test.cases import FastTenantTestCase
from django_tenants.test.client import TenantClient
from rest_framework.test import APIClient
from rest_framework import status

from bims.models import LocationSite, location_site_post_save_handler
from bims.tests.model_factories import LocationSiteF, UserF


@mock.patch('bims.models.location_site.update_location_site_context')
class TestRejectLocationSite(FastTenantTestCase):

    def setUp(self):
        self.location_site = LocationSiteF.create()
        signals.post_save.disconnect(
            location_site_post_save_handler,
            sender=LocationSite)

    def test_reject_location_site(self, mock_update_location_site_context):
        client = TenantClient(self.tenant)
        api_url = '/api/reject-location-site/'

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
        self.assertEqual(site.rejected, True)

    def tearDown(self):
        signals.post_save.connect(
            receiver=location_site_post_save_handler,
            sender=LocationSite)
