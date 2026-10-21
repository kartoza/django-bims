# coding=utf-8
"""Tests for how a layer filter is turned into a list of record ids."""
from contextlib import contextmanager
from unittest import mock

from django.contrib.gis.geos import Point
from django.core.cache import cache
from django.test import override_settings
from django_tenants.test.cases import FastTenantTestCase

from bims.models import BiologicalCollectionRecord, OgcLayer
from bims.tests.model_factories import (
    BiologicalCollectionRecordF,
    LocationSiteF,
    TaxonomyF,
    UserF,
)
from bims.utils import ogc_layer as ogc_layer_utils
from bims.utils.ogc_protection import OgcLayerTimeoutError
from bims.utils.ogc_layer import (
    OgcLayerFilterError,
    _matching_ids,
    OgcLayerOverCapError,
    get_layer_extent,
    get_layer_ids,
    visible_ids,
)

LOCMEM = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'ogc-evaluation-tests',
    }
}


@override_settings(CACHES=LOCMEM)
class TestLayerEvaluation(FastTenantTestCase):

    def setUp(self):
        cache.clear()
        self.owner = UserF.create(username='evaluation_owner')
        self.taxon = TaxonomyF.create()
        self.site = LocationSiteF.create()
        self.layer = OgcLayer.objects.create(
            name='Layer', owner=self.owner,
            query={'taxon': str(self.taxon.id)})

    def create_records(self, count, **kwargs):
        return [
            BiologicalCollectionRecordF.create(
                taxonomy=self.taxon, site=self.site, **kwargs)
            for _ in range(count)
        ]

    def test_visibility_is_checked_in_chunks(self):
        records = self.create_records(5)
        BiologicalCollectionRecord.objects.filter(
            pk=records[2].pk).update(validated=False)
        ids = sorted(r.pk for r in records)
        with mock.patch.object(ogc_layer_utils, 'VISIBILITY_CHUNK', 2):
            self.assertEqual(
                visible_ids(self.layer, ids),
                [pk for pk in ids if pk != records[2].pk])

    def test_unreadable_filter_is_a_filter_error(self):
        for error in (ValueError('bad'), TypeError('bad'), SyntaxError('bad')):
            with mock.patch(
                'bims.api_views.search.CollectionSearch.process_search',
                side_effect=error
            ):
                with self.assertRaises(OgcLayerFilterError):
                    get_layer_ids(self.layer, use_cache=False)

    def test_hidden_records_are_not_in_the_layer(self):
        records = self.create_records(3)
        BiologicalCollectionRecord.objects.filter(
            pk=records[0].pk).update(validated=False)
        self.assertEqual(
            get_layer_ids(self.layer, use_cache=False),
            sorted([records[1].pk, records[2].pk]))

    def test_ids_are_unique_and_sorted(self):
        records = self.create_records(4)
        ids = get_layer_ids(self.layer, use_cache=False)
        self.assertEqual(ids, sorted(r.pk for r in records))
        self.assertEqual(len(ids), len(set(ids)))

    def test_cap_is_enforced_on_the_matches(self):
        self.create_records(3)
        with self.settings(OGC_LAYER_MAX_RECORDS=2):
            with self.assertRaises(OgcLayerOverCapError):
                get_layer_ids(self.layer, use_cache=False)
        with self.settings(OGC_LAYER_MAX_RECORDS=3):
            self.assertEqual(
                len(get_layer_ids(self.layer, use_cache=False)), 3)

    def test_extent_does_not_search_again(self):
        self.create_records(2)
        real = ogc_layer_utils.get_matched_queryset
        with mock.patch.object(
            ogc_layer_utils, 'get_matched_queryset', side_effect=real
        ) as spy:
            extent = get_layer_extent(self.layer)
        self.assertEqual(spy.call_count, 1)
        point = self.site.geometry_point
        for value, expected in zip(
                extent, [point.x, point.y, point.x, point.y]):
            self.assertAlmostEqual(value, expected)

    def test_extent_is_merged_across_chunks(self):
        other_site = LocationSiteF.create(geometry_point=Point(25.0, 10.0))
        self.create_records(2)
        BiologicalCollectionRecordF.create(
            taxonomy=self.taxon, site=other_site)
        with mock.patch.object(ogc_layer_utils, 'VISIBILITY_CHUNK', 1):
            extent = get_layer_extent(self.layer, use_cache=False)
        points = [self.site.geometry_point, other_site.geometry_point]
        expected = [
            min(p.x for p in points), min(p.y for p in points),
            max(p.x for p in points), max(p.y for p in points)]
        for value, wanted in zip(extent, expected):
            self.assertAlmostEqual(value, wanted)
        self.assertNotEqual(extent[0], extent[2])


class FakeIds:
    """Stands in for the queryset of ids, to control what a read returns."""

    def __init__(self, rows, distinct_rows=None):
        self.rows = rows
        self.distinct_rows = distinct_rows

    def order_by(self):
        return self

    def values_list(self, *args, **kwargs):
        return self

    def distinct(self):
        return FakeIds(self.distinct_rows)

    def __getitem__(self, key):
        return self.rows[key]


class TestMatchingIds(FastTenantTestCase):

    def matched(self, rows, distinct_rows=None):
        return FakeIds(rows, distinct_rows)

    def test_ids_are_returned_sorted(self):
        self.assertEqual(
            _matching_ids(self.matched([5, 2, 9]), cap=10), [2, 5, 9])

    def test_more_than_the_cap_is_reported_as_too_many(self):
        found = _matching_ids(self.matched([1, 2, 3, 4]), cap=3)
        self.assertGreater(len(found), 3)

    def test_repeated_ids_are_removed_by_the_database_when_cut(self):
        # Three rows read for a cap of two, but only two distinct ids
        found = _matching_ids(
            self.matched([1, 1, 2], distinct_rows=[1, 2]), cap=2)
        self.assertEqual(found, [1, 2])

    def test_repeated_ids_do_not_hide_an_overflow(self):
        found = _matching_ids(
            self.matched([1, 1, 2], distinct_rows=[1, 2, 3]), cap=2)
        self.assertGreater(len(found), 2)

    def test_slow_first_attempt_is_retried_without_index_scans(self):
        calls = []

        @contextmanager
        def fake_timeout(seconds=None, avoid_index_scan=False):
            calls.append((seconds, avoid_index_scan))
            if not avoid_index_scan:
                raise OgcLayerTimeoutError('slow')
            yield

        with self.settings(OGC_LAYER_FIRST_ATTEMPT_TIMEOUT=3):
            with mock.patch.object(
                ogc_layer_utils, 'statement_timeout', fake_timeout
            ):
                found = _matching_ids(self.matched([3, 1]), cap=10)
        self.assertEqual(found, [1, 3])
        self.assertEqual(calls, [(3, False), (None, True)])

    def test_second_attempt_failure_is_reported(self):
        @contextmanager
        def always_slow(seconds=None, avoid_index_scan=False):
            raise OgcLayerTimeoutError('slow')
            yield

        with mock.patch.object(
            ogc_layer_utils, 'statement_timeout', always_slow
        ):
            with self.assertRaises(OgcLayerTimeoutError):
                _matching_ids(self.matched([1]), cap=10)
