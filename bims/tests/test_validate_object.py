import logging
import mock

from django.db.models import signals
from django.test import TestCase
from django_tenants.test.cases import FastTenantTestCase
from django_tenants.test.client import TenantClient
from rest_framework.test import APIClient
from rest_framework import status
from bims.models import LocationSite, location_site_post_save_handler
from bims.tests.model_factories import LocationSiteF, UserF

logger = logging.getLogger('bims')


@mock.patch('bims.models.location_site.update_location_site_context')
class TestValidateLocationSite(FastTenantTestCase):

    def setUp(self):
        self.client = TenantClient(self.tenant)
        self.location_site = LocationSiteF.create()
        signals.post_save.disconnect(
            location_site_post_save_handler,
            sender=LocationSite)

    def test_validate_location_site(self, mock_update_location_site_context):
        api_url = '/api/validate-location-site/'
        # Cannot merge sites without log in as superuser
        res = self.client.get(api_url, {})
        self.assertTrue(
            res.status_code == status.HTTP_302_FOUND
        )

        user = UserF.create(is_superuser=True)
        self.client.login(
            username=user.username,
            password='password'
        )

        res = self.client.get(api_url, {})
        self.assertTrue(
            res.status_code == status.HTTP_403_FORBIDDEN
        )

        site = LocationSiteF.create()
        res = self.client.get(api_url, {
            'pk': site.id
        })
        self.assertTrue(
            res.status_code == status.HTTP_200_OK
        )
        site = LocationSite.objects.get(pk=site.id)
        self.assertEqual(site.validated, True)

    def tearDown(self):
        signals.post_save.connect(
            receiver=location_site_post_save_handler,
            sender=LocationSite)
