import uuid
from unittest.mock import patch

import factory
from django.db.models import signals
from django_tenants.test.cases import FastTenantTestCase
from django_tenants.test.client import TenantClient

from preferences import preferences

from bims.models import generate_site_code
from bims.models.site_setting import SiteSetting
from django.urls import reverse
from rest_framework import status

from bims.tests.model_factories import UserF, LocationSiteF, LocationContextGroupF, LayerF
from bims.utils.site_code import SANPARK_PARK_KEY


def mocked_fetch_river_name(latitude, longitude):
    return 'GEOCONTEXT RIVER'


def mocked_fbis_catchment_generator(location_site, lat, lon, river_name):
    return 'TEST', 'CASE'


class TestGetSiteCode(FastTenantTestCase):
    @patch(
        'bims.location_site.river.fetch_river_name', mocked_fetch_river_name)
    @patch(
        'bims.utils.site_code.fbis_catchment_generator',
        mocked_fbis_catchment_generator)
    @factory.django.mute_signals(signals.pre_save, signals.post_save)
    def test_get_fbis_site_code(self):
        location_site = LocationSiteF.create()
        api_url = reverse('get-site-code') + f'?site_id={location_site.id}'
        site_setting = preferences.SiteSetting

        if not site_setting:
            site_setting = SiteSetting.objects.create()

        if site_setting:
            site_setting.site_code_generator = 'fbis'
            site_setting.save()

        client = TenantClient(self.tenant)

        user = UserF.create(is_superuser=True)
        client.login(
            username=user.username,
            password='password'
        )

        res = client.get(api_url)
        self.assertEqual(
            res.status_code, status.HTTP_200_OK
        )
        self.assertTrue(
            res.json()['river'],
            'GEOCONTEXT RIVER'
        )


    @patch('bims.utils.site_code.query_features')
    @factory.django.mute_signals(signals.pre_save, signals.post_save)
    def test_get_sanparks_site_code(self, mock_query):
        client = TenantClient(self.tenant)
        location_site = LocationSiteF.create(name='test')
        site_setting = preferences.SiteSetting

        group = LocationContextGroupF.create(
            name=SANPARK_PARK_KEY,
            key=str(uuid.uuid4()),
            layer_identifier='park_name'
        )

        user = UserF.create(is_superuser=True)
        LayerF.create(
            unique_id=group.key,
            created_by=user
        )

        mock_query.return_value = {
            'result': [
                {
                    'feature': {
                        'park_name': 'KrugerNationalPark'
                    }
                }
            ]
        }

        if not site_setting:
            site_setting = SiteSetting.objects.create()

        if site_setting:
            site_setting.default_data_source = 'sanparks'
            site_setting.save()

        site_code, catchment_data = generate_site_code(
            location_site=location_site,
            lat=location_site.latitude,
            lon=location_site.longitude
        )
        self.assertTrue(
            'KRU' in site_code
        )
