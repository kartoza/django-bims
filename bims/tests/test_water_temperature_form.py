import json
import logging
import os
from allauth.utils import get_user_model

from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse

from bims.tests.model_factories import (
    LocationSiteF
)

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
