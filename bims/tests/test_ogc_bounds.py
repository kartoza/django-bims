# coding=utf-8
"""Tests for the limits on bbox and page size of the OGC endpoints."""
import json
from unittest import mock
from urllib.parse import parse_qs, urlparse

from django.core.cache import cache
from django.db import connection
from django.test import SimpleTestCase, override_settings
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from django_tenants.test.cases import FastTenantTestCase
from django_tenants.test.client import TenantClient

from bims.models import BiologicalCollectionRecord, OgcLayer
from bims.tests.model_factories import (
    BiologicalCollectionRecordF,
    LocationSiteF,
    TaxonomyF,
    UserF,
)
from bims.utils import ogc_layer as ogc_layer_utils
from bims.utils.ogc_layer import snap_bbox

LOCMEM = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'ogc-bounds-tests',
    }
}


@override_settings(OGC_BBOX_MIN_STEP=0.001)
class TestSnapBbox(SimpleTestCase):

    def test_none_stays_none(self):
        self.assertIsNone(snap_bbox(None))

    def test_snapped_bbox_contains_the_original(self):
        for bbox in (
            (18.123, -33.987, 18.456, -33.5),
            (-10.5, 2.25, 30.75, 40.1),
            (0.0004, 0.0004, 0.0005, 0.0005),
            (-179.9, -89.9, 179.9, 89.9),
        ):
            snapped = snap_bbox(bbox)
            self.assertLessEqual(snapped[0], bbox[0] + 1e-6)
            self.assertLessEqual(snapped[1], bbox[1] + 1e-6)
            self.assertGreaterEqual(snapped[2], bbox[2] - 1e-6)
            self.assertGreaterEqual(snapped[3], bbox[3] - 1e-6)

    def test_nearby_bboxes_share_one_snapped_bbox(self):
        first = snap_bbox((18.1231, -33.9871, 18.4562, -33.5001))
        second = snap_bbox((18.1249, -33.9899, 18.4571, -33.5012))
        self.assertEqual(first, second)

    def test_distant_bboxes_do_not_share(self):
        self.assertNotEqual(
            snap_bbox((18.1, -33.9, 18.4, -33.5)),
            snap_bbox((19.1, -33.9, 19.4, -33.5)))

    def test_snapping_stays_close_to_the_request(self):
        bbox = (18.12, -33.98, 18.46, -33.5)
        snapped = snap_bbox(bbox)
        size = bbox[2] - bbox[0]
        self.assertLess(bbox[0] - snapped[0], size / 4)
        self.assertLess(snapped[2] - bbox[2], size / 4)

    def test_stays_within_the_world(self):
        snapped = snap_bbox((-190.0, -95.0, 190.0, 95.0))
        self.assertEqual(snapped, (-180.0, -90.0, 180.0, 90.0))

    def test_a_point_gets_the_smallest_step(self):
        snapped = snap_bbox((18.12345, -33.12345, 18.12345, -33.12345))
        self.assertAlmostEqual(snapped[0], 18.123)
        self.assertAlmostEqual(snapped[2], 18.124)

    def test_min_step_is_a_setting(self):
        with self.settings(OGC_BBOX_MIN_STEP=1):
            snapped = snap_bbox((18.2, -33.2, 18.3, -33.1))
        self.assertEqual(snapped, (18.0, -34.0, 19.0, -33.0))


class OgcBoundsTestCase(FastTenantTestCase):

    def setUp(self):
        overrides = self.settings(
            CACHES=LOCMEM,
            OGC_RATE_LIMIT_IP=0,
            OGC_RATE_LIMIT_LAYER=0,
            OGC_RATE_LIMIT_OWNER=0,
            OGC_RATE_LIMIT_BAD_TOKEN=0,
            OGC_RATE_LIMIT_EVALUATIONS=0,
        )
        overrides.enable()
        self.addCleanup(overrides.disable)
        cache.clear()
        self.client = TenantClient(self.tenant)
        self.owner = UserF.create(username='bounds_owner')
        self.taxon = TaxonomyF.create()
        self.site = LocationSiteF.create()
        self.layer = OgcLayer.objects.create(
            name='Layer', owner=self.owner,
            query={'taxon': str(self.taxon.id)})
        self.token = self.layer.raw_token

    def items(self, **params):
        url = reverse('ogc-items', kwargs={
            'token': self.token, 'collection_id': 'records'})
        return self.client.get(url, params)

    def create_records(self, count):
        return [
            BiologicalCollectionRecordF.create(
                taxonomy=self.taxon, site=self.site)
            for _ in range(count)
        ]


class TestBboxCache(OgcBoundsTestCase):

    def test_nearby_bboxes_evaluate_the_layer_once(self):
        self.create_records(2)
        self.items()
        real = ogc_layer_utils.get_layer_queryset
        with mock.patch.object(
            ogc_layer_utils, 'get_layer_queryset', side_effect=real
        ) as spy:
            first = self.items(bbox='-39.5,-39.5,39.5,39.5')
            second = self.items(bbox='-39.7,-39.2,39.1,39.9')
        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 200)
        self.assertEqual(spy.call_count, 1)

    def test_bbox_entries_expire_sooner_than_layer_entries(self):
        self.create_records(1)
        timeouts = []
        real_set = cache.set

        def spy(key, value, timeout=None, *args, **kwargs):
            timeouts.append(timeout)
            return real_set(key, value, timeout, *args, **kwargs)

        with self.settings(
            OGC_BBOX_CACHE_TTL=11, OGC_LAYER_COUNT_CACHE_TTL=222
        ):
            with mock.patch.object(cache, 'set', side_effect=spy):
                self.items()
                whole_layer = set(timeouts)
                del timeouts[:]
                self.items(bbox='-39.5,-39.5,39.5,39.5')
        self.assertEqual(whole_layer, {222})
        self.assertEqual(set(timeouts), {11})

    def test_non_finite_bbox_is_rejected(self):
        for bbox in ('nan,0,1,1', '0,0,inf,1', '-inf,0,1,1'):
            response = self.items(bbox=bbox)
            self.assertEqual(response.status_code, 400, bbox)

    def test_bbox_still_filters_records(self):
        self.create_records(2)
        far = self.items(bbox='100,60,101,61')
        self.assertEqual(far.json()['numberMatched'], 0)


class TestResponseCap(OgcBoundsTestCase):

    def uuids(self, response):
        return [f['id'] for f in response.json()['features']]

    def next_offset(self, response):
        for link in response.json()['links']:
            if link['rel'] == 'next':
                query = parse_qs(urlparse(link['href']).query)
                return int(query['offset'][0])
        return None

    def test_small_pages_are_untouched(self):
        self.create_records(3)
        response = self.items(limit=3)
        self.assertEqual(response.json()['numberReturned'], 3)
        self.assertIsNone(self.next_offset(response))

    def test_page_stops_at_the_size_cap_and_points_to_the_rest(self):
        self.create_records(3)
        with self.settings(OGC_RESPONSE_MAX_BYTES=1):
            response = self.items(limit=3)
        body = response.json()
        self.assertEqual(body['numberMatched'], 3)
        self.assertEqual(body['numberReturned'], 1)
        self.assertEqual(self.next_offset(response), 1)

    def test_following_next_links_returns_every_record_once(self):
        records = self.create_records(4)
        seen, offset = [], 0
        with self.settings(OGC_RESPONSE_MAX_BYTES=1):
            for _ in range(10):
                response = self.items(limit=4, offset=offset)
                seen += self.uuids(response)
                offset = self.next_offset(response)
                if offset is None:
                    break
        self.assertEqual(
            sorted(seen), sorted(str(r.uuid) for r in records))

    def test_cut_page_skips_records_that_stopped_being_visible(self):
        first, second, third = self.create_records(3)
        self.items()  # cache the ids
        # The second record disappears from the layer while its id is cached
        BiologicalCollectionRecord.objects.filter(
            pk=second.pk).update(validated=False)
        with self.settings(OGC_RESPONSE_MAX_BYTES=1):
            response = self.items(limit=3)
        self.assertEqual(self.uuids(response), [str(first.uuid)])
        # The third record sits at position 2 of the cached ids
        self.assertEqual(self.next_offset(response), 2)

    def test_one_feature_is_always_returned(self):
        self.create_records(1)
        with self.settings(OGC_RESPONSE_MAX_BYTES=1):
            response = self.items()
        self.assertEqual(response.json()['numberReturned'], 1)

    def test_response_is_valid_geojson(self):
        self.create_records(2)
        response = self.items()
        body = json.loads(response.content)
        self.assertEqual(body['type'], 'FeatureCollection')
        self.assertEqual(response['Content-Type'], 'application/geo+json')


class TestQueryCount(OgcBoundsTestCase):

    def make_full_records(self, count):
        records = []
        for index in range(count):
            records.append(BiologicalCollectionRecordF.create(
                taxonomy=TaxonomyF.create(),
                site=LocationSiteF.create(),
                owner=UserF.create(username='n1_owner_%d' % index),
                collector_user=UserF.create(username='n1_collector_%d' % index),
            ))
        return records

    def count_queries(self, limit, ids):
        with mock.patch(
            'bims.api_views.ogc_features.get_layer_ids', return_value=ids
        ):
            self.items(limit=limit)  # warm anything else that is cached
            with CaptureQueriesContext(connection) as queries:
                response = self.items(limit=limit)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['numberReturned'], limit)
        return len(queries)

    def test_items_query_count_does_not_grow_with_the_page(self):
        records = self.make_full_records(12)
        ids = sorted(r.pk for r in records)
        small = self.count_queries(2, ids)
        large = self.count_queries(12, ids)
        self.assertEqual(
            small, large,
            'Items runs more queries for a larger page: N+1 in the '
            'serializer or SELECT_RELATED')
