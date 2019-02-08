import json
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIRequestFactory
from bims.tests.model_factories import DataSourceF


class TestApiView(TestCase):
    """Test autocomplete search"""

    def setUp(self):
        self.factory = APIRequestFactory()

    def test_data_search_auto_complete(self):
        self.data_source_1 = DataSourceF.create(
            name='foo bar'
        )
        self.data_source_2 = DataSourceF.create(
            name='foo test'
        )
        url_path = '{url}?term={search}'.format(
            url=reverse('data-source-autocomplete-search'),
            search='foo'
        )
        r = self.client.get(
            url_path,
            **{'HTTP_X_REQUESTED_WITH': 'XMLHttpRequest'})
        response_data = json.loads(r.content)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(len(response_data), 2)
