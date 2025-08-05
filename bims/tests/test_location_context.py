import os
import mock
import json

from cloud_native_gis.tests.model_factories import create_user
from django.test import TestCase, override_settings

from bims.utils.location_context import get_location_context_data
from bims.tests.model_factories import LocationSiteF, LocationContextGroupF, UserF
from bims.models.location_context_group import LocationContextGroup
from bims.models.location_context import LocationContext
from cloud_native_gis.models import Layer

test_data_directory = os.path.join(
    os.path.dirname(os.path.realpath(__file__)), 'data')

def mocked_location_context_data(*args, **kwargs):
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

    @override_settings(GEOCONTEXT_URL="test.gecontext.com")
    @mock.patch('requests.get', mock.Mock(
        side_effect=mocked_location_context_data))
    def test_get_location_context_data(self):
        get_location_context_data(
            group_keys=self.location_context_group_keys
        )
        self.assertTrue(
            LocationContextGroup.objects.filter(
                geocontext_group_key='hydrological_regions',
            ).exists()
        )
        self.assertTrue(
            LocationContext.objects.filter(
                group__geocontext_group_key='hydrological_regions',
                site=self.site
            ).exists()
        )
        self.assertEqual(
            LocationContext.objects.get(
                group__key='value_with_comma',
                group__geocontext_group_key='hydrological_regions',
                site=self.site
            ).value,
            'test, comma'
        )

    @override_settings(GEOCONTEXT_URL="test.gecontext.com")
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


class TestAddLocationContext(TestCase):
    def setUp(self) -> None:
        pass

    @mock.patch('bims.models.location_site.query_features')
    def test_add_location_context_from_native_layer(self, mock_query_features):
        location_site = LocationSiteF.create()
        user_1 = create_user(password='password')
        layer = Layer.objects.create(
            name='layer_test',
            created_by=user_1
        )
        context_key = 'test_context_key'
        full_group_key = f'{layer.unique_id}:{context_key}'

        mock_query_features.return_value = {
            'result': [{'feature': {context_key: 'some_value'}}]
        }

        location_site.add_context_group(full_group_key)

        mock_query_features.assert_called_once_with(
            table_name=layer.query_table_name,
            field_names=[context_key],
            coordinates=[(location_site.longitude, location_site.latitude)],
            tolerance=0
        )

        location_context_group = LocationContextGroup.objects.filter(
            geocontext_group_key=layer.unique_id,
            key=layer.unique_id,
            name='layer_test'
        )

        self.assertTrue(location_context_group.exists())

        new_layer = Layer.objects.create(
            name='layer_test_2',
            created_by=user_1
        )
        LocationContextGroupF.create(
            geocontext_group_key=new_layer.unique_id,
            key=new_layer.unique_id,
            name='Unchanged'
        )
        full_group_key = f'{new_layer.unique_id}:{context_key}'
        location_site.add_context_group(full_group_key)

        location_context_group = LocationContextGroup.objects.filter(
            geocontext_group_key=new_layer.unique_id,
            key=new_layer.unique_id,
            name='Unchanged'
        )
        self.assertTrue(location_context_group.exists())

        location_context_values = LocationContext.objects.filter(
            site=location_site,
            value='some_value'
        )

        self.assertEqual(
            location_context_values.count(),
            2
        )
