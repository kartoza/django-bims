from django.test import TestCase
from unittest.mock import patch

from requests import HTTPError

from bims.utils.feature_info import get_feature_info_from_wms


class TestGetFeatureInfoFromWMS(TestCase):

    @patch('requests.get')
    def test_successful_request(self, mock_get):
        mock_response = mock_get.return_value
        mock_response.status_code = 200
        mock_response.json.return_value = {'feature': 'some_info'}

        result = get_feature_info_from_wms(
            "http://your.wms.server",
            "your_layer", "EPSG:4326", 40.7128, -74.0060, 800, 600)

        self.assertEqual(result, {'feature': 'some_info'})

    @patch('requests.get')
    def test_unsuccessful_request(self, mock_get):
        mock_response = mock_get.return_value
        mock_response.status_code = 404

        result = get_feature_info_from_wms(
            "http://your.wms.server",
            "your_layer", "EPSG:4326", 40.7128, -74.0060, 800, 600)

        self.assertEqual(result, None)

    @patch('requests.get')
    def test_request_exception(self, mock_get):
        mock_get.side_effect = HTTPError()

        result = get_feature_info_from_wms(
            "http://your.wms.server",
            "your_layer", "EPSG:4326", 40.7128, -74.0060, 800, 600)

        self.assertEqual(result, None)
