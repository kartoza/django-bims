# coding=utf-8
"""Tests for the HTTP validators on the OGC API - Features endpoints."""
from unittest import mock

from django.core.cache import cache
from django.urls import reverse
from django_tenants.test.cases import FastTenantTestCase
from django_tenants.test.client import TenantClient

from bims.models import OgcLayer
from bims.tests.model_factories import (
    BiologicalCollectionRecordF,
    LocationSiteF,
    TaxonomyF,
    UserF,
)

LOCMEM = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'ogc-http-cache-tests',
    }
}
DUMMY = {
    'default': {'BACKEND': 'django.core.cache.backends.dummy.DummyCache'}
}


class OgcHttpCacheTestCase(FastTenantTestCase):

    def setUp(self):
        overrides = self.settings(
            CACHES=LOCMEM,
            OGC_RATE_LIMIT_IP=0,
            OGC_RATE_LIMIT_LAYER=0,
            OGC_RATE_LIMIT_OWNER=0,
            OGC_RATE_LIMIT_BAD_TOKEN=0,
            OGC_RATE_LIMIT_EVALUATIONS=0,
            OGC_HTTP_CACHE_MAX_AGE=60,
        )
        overrides.enable()
        self.addCleanup(overrides.disable)
        cache.clear()
        self.client = TenantClient(self.tenant)
        self.owner = UserF.create(username='http_cache_owner')
        self.taxon = TaxonomyF.create()
        self.site = LocationSiteF.create()
        for _ in range(3):
            BiologicalCollectionRecordF.create(
                taxonomy=self.taxon, site=self.site)
        self.layer = OgcLayer.objects.create(
            name='Layer', owner=self.owner,
            query={'taxon': str(self.taxon.id)})
        self.token = self.layer.raw_token

    def url(self, name, **kwargs):
        kwargs['token'] = self.token
        return reverse(name, kwargs=kwargs)

    def items(self):
        return self.url('ogc-items', collection_id='records')


class TestItemsValidators(OgcHttpCacheTestCase):

    def test_response_carries_validators_and_cache_control(self):
        response = self.client.get(self.items())
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response['ETag'].startswith('W/"'))
        self.assertIn('Last-Modified', response)
        self.assertEqual(response['Cache-Control'], 'private, max-age=60')

    def test_matching_etag_gets_304_without_reading_data(self):
        etag = self.client.get(self.items())['ETag']
        with mock.patch(
            'bims.api_views.ogc_features.get_layer_ids',
            side_effect=AssertionError('data must not be read')
        ):
            response = self.client.get(
                self.items(), HTTP_IF_NONE_MATCH=etag)
        self.assertEqual(response.status_code, 304)
        self.assertEqual(response.content, b'')
        self.assertEqual(response['ETag'], etag)
        self.assertEqual(response['Cache-Control'], 'private, max-age=60')

    def test_other_etag_gets_a_full_response(self):
        self.client.get(self.items())
        response = self.client.get(
            self.items(), HTTP_IF_NONE_MATCH='W/"something-else"')
        self.assertEqual(response.status_code, 200)

    def test_if_modified_since_gets_304(self):
        first = self.client.get(self.items())
        response = self.client.get(
            self.items(), HTTP_IF_MODIFIED_SINCE=first['Last-Modified'])
        self.assertEqual(response.status_code, 304)

    def test_pages_have_different_etags(self):
        first = self.client.get(self.items() + '?limit=1&offset=0')
        second = self.client.get(self.items() + '?limit=1&offset=1')
        self.assertNotEqual(first['ETag'], second['ETag'])

    def test_etag_for_a_page_is_stable(self):
        first = self.client.get(self.items() + '?limit=2')
        second = self.client.get(self.items() + '?limit=2')
        self.assertEqual(first['ETag'], second['ETag'])

    def test_etag_changes_when_the_layer_is_rebuilt(self):
        with mock.patch('time.time', return_value=1_000_000):
            first = self.client.get(self.items())
        cache.clear()
        with mock.patch('time.time', return_value=1_000_500):
            second = self.client.get(self.items())
        self.assertNotEqual(first['ETag'], second['ETag'])
        stale = self.client.get(
            self.items(), HTTP_IF_NONE_MATCH=first['ETag'])
        self.assertEqual(stale.status_code, 200)

    def test_bbox_requests_have_their_own_etag(self):
        plain = self.client.get(self.items())
        boxed = self.client.get(self.items() + '?bbox=-180,-90,180,90')
        self.assertEqual(boxed.status_code, 200)
        self.assertNotEqual(plain['ETag'], boxed['ETag'])
        again = self.client.get(
            self.items() + '?bbox=-180,-90,180,90',
            HTTP_IF_NONE_MATCH=boxed['ETag'])
        self.assertEqual(again.status_code, 304)

    def test_revoked_layer_is_not_answered_with_304(self):
        etag = self.client.get(self.items())['ETag']
        self.layer.is_active = False
        self.layer.save()
        response = self.client.get(self.items(), HTTP_IF_NONE_MATCH=etag)
        self.assertEqual(response.status_code, 404)

    def test_errors_are_not_given_validators(self):
        response = self.client.get(self.items() + '?limit=abc')
        self.assertEqual(response.status_code, 400)
        self.assertNotIn('ETag', response)
        self.assertNotIn('Cache-Control', response)

    def test_zero_max_age_asks_clients_to_revalidate(self):
        with self.settings(OGC_HTTP_CACHE_MAX_AGE=0):
            response = self.client.get(self.items())
        self.assertEqual(response['Cache-Control'], 'private, no-cache')
        self.assertIn('ETag', response)

    def test_etag_header_is_exposed_to_browsers(self):
        response = self.client.get(self.items())
        self.assertIn('ETag', response['Access-Control-Expose-Headers'])

    def test_no_validators_without_a_cache(self):
        with self.settings(CACHES=DUMMY):
            response = self.client.get(self.items())
            again = self.client.get(
                self.items(), HTTP_IF_NONE_MATCH='W/"anything"')
        self.assertEqual(response.status_code, 200)
        self.assertNotIn('ETag', response)
        self.assertEqual(again.status_code, 200)


class TestOtherEndpointValidators(OgcHttpCacheTestCase):

    def test_static_documents_are_revalidated_without_data(self):
        for name, kwargs in (
            ('ogc-landing-page', {}),
            ('ogc-conformance', {}),
            ('ogc-api', {}),
        ):
            url = self.url(name, **kwargs)
            first = self.client.get(url)
            self.assertEqual(first.status_code, 200, name)
            self.assertNotIn('Last-Modified', first)
            self.assertEqual(first['Cache-Control'], 'private, max-age=60')
            with mock.patch(
                'bims.api_views.ogc_features.get_layer_ids',
                side_effect=AssertionError('data must not be read')
            ):
                again = self.client.get(
                    url, HTTP_IF_NONE_MATCH=first['ETag'])
            self.assertEqual(again.status_code, 304, name)

    def test_documents_have_their_own_etags(self):
        etags = {
            self.client.get(self.url(name))['ETag']
            for name in ('ogc-landing-page', 'ogc-conformance', 'ogc-api')
        }
        self.assertEqual(len(etags), 3)

    def test_collection_follows_the_layer_data(self):
        url = self.url('ogc-collection', collection_id='records')
        first = self.client.get(url)
        self.assertEqual(first.status_code, 200)
        self.assertIn('Last-Modified', first)
        again = self.client.get(url, HTTP_IF_NONE_MATCH=first['ETag'])
        self.assertEqual(again.status_code, 304)
        cache.clear()
        with mock.patch('time.time', return_value=2_000_000_000):
            rebuilt = self.client.get(url)
        self.assertNotEqual(first['ETag'], rebuilt['ETag'])

    def test_collections_list_has_validators(self):
        url = self.url('ogc-collections')
        first = self.client.get(url)
        again = self.client.get(url, HTTP_IF_NONE_MATCH=first['ETag'])
        self.assertEqual(again.status_code, 304)

    def test_single_feature_has_validators(self):
        from bims.models import BiologicalCollectionRecord
        record = BiologicalCollectionRecord.objects.filter(
            taxonomy=self.taxon).first()
        url = self.url(
            'ogc-item', collection_id='records', item_id=str(record.uuid))
        first = self.client.get(url)
        self.assertEqual(first.status_code, 200)
        again = self.client.get(url, HTTP_IF_NONE_MATCH=first['ETag'])
        self.assertEqual(again.status_code, 304)

    def test_unknown_collection_does_not_match_a_valid_etag(self):
        valid = self.client.get(
            self.url('ogc-collection', collection_id='records'))
        response = self.client.get(
            self.url('ogc-collection', collection_id='other'),
            HTTP_IF_NONE_MATCH=valid['ETag'])
        self.assertEqual(response.status_code, 404)
