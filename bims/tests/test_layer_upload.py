from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.urls import reverse
import os
from bims.tests.model_factories import (
    Boundary
)

test_data_directory = os.path.join(
    os.path.dirname(os.path.realpath(__file__)), 'data')

User = get_user_model()


class TestLayerUpload(TestCase):
    """
    Tests layer upload view
    """
    def setUp(self):
        self.user = User.objects.create_user('testuser', 'test@example.com', 'password')
        self.client = Client()

    def test_upload_valid_geojson(self):
        # Path to a valid GeoJSON file
        self.client.login(username='testuser', password='password')
        valid_geojson_path = os.path.join(test_data_directory, 'geojson_test.json')
        with open(valid_geojson_path, 'rb') as geojson:
            response = self.client.post(reverse('layer-upload-view'),
                                        {
                                            'geojson_file': geojson,
                                            'name': 'boundary1',
                                            'boundary_type_name': 'test'})
        self.assertEqual(response.status_code, 201)
        self.assertIn('message', response.json())
        self.assertEqual('Layer successfully uploaded and saved.', response.json()['message'])
        self.assertTrue(Boundary.objects.filter(name='boundary1').exists())
