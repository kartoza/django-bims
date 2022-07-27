from unittest.mock import patch

import factory
from django.db.models import signals

from bims.models.site_setting import SiteSetting
from django.test import TestCase, override_settings
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status

from bims.tests.model_factories import UserF, LocationSiteF


def mocked_fetch_river_name(latitude, longitude):
    return 'GEOCONTEXT RIVER'


def mocked_fbis_catchment_generator(location_site, lat, lon, river_name):
    return 'TEST', 'CASE'


class TestGetSiteCode(TestCase):

    @patch(
        'bims.location_site.river.fetch_river_name', mocked_fetch_river_name)
    @patch(
        'bims.utils.site_code.fbis_catchment_generator',
        mocked_fbis_catchment_generator)
    @factory.django.mute_signals(signals.pre_save, signals.post_save)
    def test_get_fbis_site_code(self):
        location_site = LocationSiteF.create()
        api_url = reverse('get-site-code') + f'?site_id={location_site.id}'
        site_setting = SiteSetting.objects.first()

        if site_setting:
            site_setting.site_code_generator = 'fbis'
            site_setting.save()

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
        self.assertTrue(
            res.json()['river'],
            'GEOCONTEXT RIVER'
        )
