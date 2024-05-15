from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.urls import reverse
import os

from django_tenants.test.cases import FastTenantTestCase
from django_tenants.test.client import TenantClient

from bims.tests.model_factories import (
    Boundary
)
from django.contrib.messages import get_messages

test_data_directory = os.path.join(
    os.path.dirname(os.path.realpath(__file__)), 'data')

User = get_user_model()


class TestLayerUpload(FastTenantTestCase):
    """
    Tests layer upload view
    """
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='password',
            is_superuser=True)
        self.client = TenantClient(self.tenant)

    def test_upload_valid_geojson(self):
        # Path to a valid GeoJSON file
        self.client.login(username='testuser', password='password')
        valid_geojson_path = os.path.join(test_data_directory, 'geojson_test.json')
        with open(valid_geojson_path, 'rb') as geojson:
            response = self.client.post(reverse('layer-upload-view'),
                                        {
                                            'geojson_file': geojson,
                                            'name': 'boundary1'})
        self.assertEqual(response.status_code, 302)
        self.assertEqual('Layer successfully uploaded and saved.',
                         str(list(get_messages(response.wsgi_request))[0]))
        self.assertTrue(Boundary.objects.filter(name='boundary1').exists())
