import os
import mock
import json
from django.test import TestCase

from bims.utils.location_context import get_location_context_data
from bims.tests.model_factories import LocationSiteF, LocationContextGroupF
from bims.models.location_context_group import LocationContextGroup
from bims.models.location_context import LocationContext


test_data_directory = os.path.join(
    os.path.dirname(os.path.realpath(__file__)), 'data')

def mocked_location_context_data(url):
    class MockResponse:
        def __init__(self, json_data, status_code):
            self.json_data = json_data
            self.status_code = status_code

        def json(self):
            return self.json_data

    response_file = 'geocontext_data.json'
    response_path = os.path.join(
        test_data_directory, response_file)
    if os.path.exists(response_path):
        response_data = open(response_path)
        json_data = response_data.read()
        response_data.close()
        return MockResponse(json.loads(json_data), 200)
    return ''


class TestLocationContext(TestCase):
    def setUp(self) -> None:
        self.site = LocationSiteF.create()
        self.location_context_group_keys = 'group1'

    @mock.patch('requests.get', mock.Mock(
        side_effect=mocked_location_context_data))
    def test_get_location_context_data(self):
        get_location_context_data(
            group_keys=self.location_context_group_keys
        )
        self.assertTrue(
            LocationContextGroup.objects.filter(
                key='hydrological_regions',
            ).exists()
        )
        self.assertTrue(
            LocationContext.objects.filter(
                group__key='hydrological_regions',
                site=self.site
            ).exists()
        )

    @mock.patch('requests.get', mock.Mock(
        side_effect=mocked_location_context_data))
    def test_get_location_context_data_multiple_groups(self):
        LocationContextGroupF.create(
            id=1,
            key='hydrological_regions',
            geocontext_group_key='group1'
        )
        LocationContextGroupF.create(
            id=2,
            key='hydrological_regions',
            geocontext_group_key='group1'
        )
        get_location_context_data(
            group_keys=self.location_context_group_keys
        )
        self.assertEqual(
            LocationContextGroup.objects.filter(
                key='hydrological_regions',
            ).count(), 1
        )
        self.assertTrue(
            LocationContextGroup.objects.filter(
                key='hydrological_regions',
                id=1
            ).exists()
        )
