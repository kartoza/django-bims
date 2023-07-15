import json
import logging
import os
from datetime import datetime

from allauth.utils import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.db.models import signals

from django.test import TestCase, RequestFactory, override_settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
import factory

from bims.api_views.thermal_data import WaterTemperatureThresholdApiView
from bims.tests.model_factories import (
    LocationSiteF, WaterTemperatureF, WaterTemperatureThresholdF
)
from bims.models.water_temperature import WaterTemperatureThreshold

logger = logging.getLogger('bims')
test_data_directory = os.path.join(
    os.path.dirname(os.path.realpath(__file__)), 'data')


class TestWaterTemperatureForm(TestCase):

    def setUp(self):
        user = get_user_model().objects.create(
            is_staff=True,
            is_active=True,
            is_superuser=True,
            username='@.test')
        user.set_password('psst')
        user.save()
        self.location_site = LocationSiteF.create()
        self.hourly_data = os.path.join(
            test_data_directory, 'hourly.csv'
        )

    def test_upload_without_login(self):
        response = self.client.post(
            reverse('upload-water-temperature'),
        )
        self.assertEqual(
            response.status_code,
            302
        )

    def test_validate_data_without_login(self):
        csv_file = SimpleUploadedFile(
            'file.csv', b'file_content',
            content_type='text/csv')
        response = self.client.post(
            reverse('validate-water-temperature'),
            {
                'water_file': csv_file
            }
        )
        self.assertEqual(
            response.status_code,
            302
        )

    def test_validate_data_with_login(self):
        # login as superuser
        self.client.login(
            username='@.test',
            password='psst'
        )
        response = self.client.post(
            reverse('validate-water-temperature'),
            {
                'edit': 'true'
            }
        )
        self.assertEqual(
            response.status_code,
            200
        )

    def test_validate_correct_data(self):
        self.client.login(
            username='@.test',
            password='psst'
        )
        hourly_data = open(self.hourly_data, 'rb')
        water_file = SimpleUploadedFile(
            'file.csv',
            hourly_data.read(),
            content_type='text/csv'
        )
        hourly_data.close()
        response = self.client.post(
            reverse('validate-water-temperature'),
            {
                'water_file': water_file,
                'format': '%d/%m/%Y',
                'interval': '1',
                'start_time': '00:00',
                'end_time': '23:00'
            }
        )
        response_content = json.loads(response.content)
        self.assertEqual(
            response_content['status'],
            'success'
        )


class WaterTemperatureThresholdApiViewTest(TestCase):

    @factory.django.mute_signals(signals.pre_save, signals.post_save)
    def setUp(self):
        self.factory = RequestFactory()
        self.user = get_user_model().objects.create(
            is_staff=False,
            is_active=True,
            is_superuser=False,
            username='@.test')
        self.user.set_password('psst')
        self.user.save()

        self.superuser = get_user_model().objects.create(
            is_staff=True,
            is_active=True,
            is_superuser=True,
            username='@.superuser')
        self.superuser.set_password('psst')
        self.superuser.save()

        self.view = WaterTemperatureThresholdApiView.as_view()
        self.location_site = LocationSiteF.create()
        self.water_temperature = WaterTemperatureF.create(
            owner=self.user,
            date_time=datetime.today(),
            is_daily=True,
            value=1,
            maximum=10,
            minimum=12,
        )
        self.water_temperature_threshold = WaterTemperatureThresholdF.create(
            location_site=self.location_site,
            upper_maximum_threshold=25,
            lower_maximum_threshold=15,
            upper_minimum_threshold=10,
            lower_minimum_threshold=5,
            upper_mean_threshold=20,
            lower_mean_threshold=15,
            upper_record_length=30,
            lower_record_length=20,
            upper_degree_days=200,
            lower_degree_days=150
        )

    def test_get_threshold(self):
        request = self.factory.get(
            '/water_temperature_threshold/',
            {'location_site': self.location_site.id}
        )
        request.user = self.user
        response = self.view(request)

        response_data = json.loads(response.content)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response_data['maximum_threshold'], 25)
        self.assertEqual(response_data['minimum_threshold'], 10)
        self.assertEqual(response_data['mean_threshold'], 20)
        self.assertEqual(response_data['record_length'], 30)
        self.assertEqual(response_data['degree_days'], 200)

    @override_settings(CSRF_COOKIE_SECURE=False)
    def test_post_threshold_authenticated(self):
        self.client.login(
            username='@.test',
            password='psst'
        )
        post_dict = {
            'location_site': self.location_site.id,
            'water_temperature': self.water_temperature.id,
            'maximum_threshold': 26
        }
        response = self.client.post(
            '/api/water-temperature-threshold/?location_site={site}&water_temperature={temp}'.format(
                site=self.location_site.id,
                temp=self.water_temperature.id
            ),
            post_dict
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b'Threshold updated successfully.')
        self.assertEqual(WaterTemperatureThreshold.objects.first().upper_maximum_threshold, 26)

    def test_post_threshold_unauthenticated(self):
        request = self.factory.post(
            '/api/water-temperature-threshold/?location_site={site}&water_temperature={temp}'.format(
                site=self.location_site.id,
                temp=self.water_temperature.id
            ),
            {
                'maximum_threshold': 26}
        )
        request.user = AnonymousUser()
        response = self.view(request)
        self.assertEqual(response.status_code, 404)
