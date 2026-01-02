import json
from datetime import date

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from django_tenants.test.cases import FastTenantTestCase
from django_tenants.test.client import TenantClient

from bims.models.upload_session import UploadSession
from bims.tests.model_factories import LocationSiteF
from climate.models import Climate


class ClimateSiteViewTests(FastTenantTestCase):
    def setUp(self):
        self.client = TenantClient(self.tenant)
        self.location_site = LocationSiteF.create(site_code='CLIM001')
        Climate.objects.create(
            location_site=self.location_site,
            station_name='Station A',
            date=date(2024, 1, 15),
            avg_temperature=20.0,
            min_temperature=10.0,
            max_temperature=30.0,
            avg_humidity=40.0,
            min_humidity=35.0,
            max_humidity=50.0,
            avg_windspeed=5.0,
            daily_rainfall=5.0,
        )
        Climate.objects.create(
            location_site=self.location_site,
            station_name='Station A',
            date=date(2024, 2, 15),
            avg_temperature=22.0,
            min_temperature=12.0,
            max_temperature=32.0,
            avg_humidity=45.0,
            min_humidity=38.0,
            max_humidity=55.0,
            avg_windspeed=6.0,
            daily_rainfall=10.0,
        )

    def test_site_view_builds_monthly_payload(self):
        url = reverse('climate:climate-site', kwargs={'site_id': self.location_site.id})
        response = self.client.get(url, {'siteId': self.location_site.id})

        self.assertEqual(response.status_code, 200)
        payload = json.loads(response.context['chart_payload'])
        self.assertEqual(payload['labels'], ['Jan 2024', 'Feb 2024'])
        self.assertEqual(payload['temperature']['avg'][0], 20.0)
        self.assertEqual(payload['temperature']['max'][1], 32.0)
        self.assertEqual(payload['rainfall']['total'][1], 10.0)
        self.assertTrue(response.context['availability']['temperature'])
        self.assertTrue(response.context['availability']['rainfall'])


class ClimateUploadViewTests(FastTenantTestCase):
    def setUp(self):
        self.client = TenantClient(self.tenant)
        User = get_user_model()
        self.user = User.objects.create_user(
            username='uploader',
            email='uploader@example.com',
            password='test-pass'
        )
        self.user.is_superuser = True
        self.user.is_staff = True
        self.user.save()
        self.session = UploadSession.objects.create(
            uploader=self.user,
            category='climate',
            progress='1/2',
            process_file=SimpleUploadedFile('climate.csv', b'site,data')
        )
        self.url = reverse('climate:climate-upload')

    def test_upload_view_requires_auth(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith('/accounts/login/'))

    def test_upload_view_lists_sessions(self):
        self.client.login(username='uploader', password='test-pass')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        upload_sessions = list(response.context['upload_sessions'])
        self.assertEqual(upload_sessions, [self.session])
        finished_sessions = response.context['finished_sessions']
        self.assertEqual(finished_sessions.count(), 0)
