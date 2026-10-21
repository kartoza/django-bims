# coding=utf-8
"""Tests for the cost controls of OGC layers: counters, auto-disable,
owner limit, kill switch and slow request log."""
from datetime import timedelta
from unittest import mock

from django.contrib.admin.sites import AdminSite
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.test import RequestFactory
from django.urls import reverse
from django.utils import timezone
from django_tenants.test.cases import FastTenantTestCase
from django_tenants.test.client import TenantClient

from bims.admin import OgcLayerAdmin
from bims.models import OgcLayer
from bims.tests.model_factories import (
    BiologicalCollectionRecordF,
    LocationSiteF,
    TaxonomyF,
    UserF,
)
from bims.utils import ogc_layer as ogc_layer_utils
from bims.utils.ogc_layer import get_layer_extent, get_layer_ids
from bims.utils.ogc_protection import OgcLayerTimeoutError

LOCMEM = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'ogc-cost-control-tests',
    }
}


class CostControlTestCase(FastTenantTestCase):

    def setUp(self):
        overrides = self.settings(
            CACHES=LOCMEM,
            OGC_RATE_LIMIT_IP=0,
            OGC_RATE_LIMIT_LAYER=0,
            OGC_RATE_LIMIT_OWNER=0,
            OGC_RATE_LIMIT_BAD_TOKEN=0,
            OGC_RATE_LIMIT_EVALUATIONS=0,
            OGC_LAYER_MAX_FAILURES=3,
            OGC_MAX_LAYERS_PER_OWNER=20,
            OGC_LAYERS_ENABLED=True,
            OGC_SLOW_REQUEST_SECONDS=3,
        )
        overrides.enable()
        self.addCleanup(overrides.disable)
        cache.clear()
        self.client = TenantClient(self.tenant)
        self.owner = UserF.create(username='cost_owner')
        self.taxon = TaxonomyF.create()
        self.site = LocationSiteF.create()
        BiologicalCollectionRecordF.create(
            taxonomy=self.taxon, site=self.site)
        self.layer = self.create_layer()

    def create_layer(self, **kwargs):
        kwargs.setdefault('query', {'taxon': str(self.taxon.id)})
        return OgcLayer.objects.create(
            name='Layer', owner=self.owner, **kwargs)

    def items(self, layer=None, **params):
        layer = layer or self.layer
        url = reverse('ogc-items', kwargs={
            'token': layer.raw_token, 'collection_id': 'records'})
        return self.client.get(url, params)


class TestFailureTracking(CostControlTestCase):

    def test_failures_are_counted(self):
        self.layer.record_failure()
        self.layer.record_failure()
        self.layer.refresh_from_db()
        self.assertEqual(self.layer.failure_count, 2)
        self.assertTrue(self.layer.is_active)

    def test_layer_is_switched_off_at_the_limit(self):
        results = [self.layer.record_failure() for _ in range(3)]
        self.assertEqual(results, [False, False, True])
        self.layer.refresh_from_db()
        self.assertFalse(self.layer.is_active)
        self.assertIn('3', self.layer.disabled_reason)

    def test_no_limit_means_never_switched_off(self):
        with self.settings(OGC_LAYER_MAX_FAILURES=0):
            for _ in range(10):
                self.assertFalse(self.layer.record_failure())
        self.layer.refresh_from_db()
        self.assertTrue(self.layer.is_active)
        self.assertEqual(self.layer.failure_count, 10)

    def test_unsaved_layer_is_ignored(self):
        self.assertFalse(OgcLayer(name='x', owner=self.owner).record_failure())

    def test_success_resets_the_failures(self):
        self.layer.record_failure()
        self.layer.record_evaluation(250)
        self.layer.refresh_from_db()
        self.assertEqual(self.layer.failure_count, 0)
        self.assertEqual(self.layer.last_evaluation_ms, 250)
        self.assertIsNotNone(self.layer.last_evaluated)

    def test_reset_failures_clears_the_reason(self):
        for _ in range(3):
            self.layer.record_failure()
        self.layer.reset_failures()
        self.layer.refresh_from_db()
        self.assertEqual(self.layer.failure_count, 0)
        self.assertEqual(self.layer.disabled_reason, '')

    def test_add_requests_adds_to_the_database_value(self):
        self.layer.add_requests(5)
        self.layer.add_requests(2)
        self.layer.add_requests(0)
        self.layer.refresh_from_db()
        self.assertEqual(self.layer.request_count, 7)


class TestEvaluationTracking(CostControlTestCase):

    def test_evaluation_time_is_stored(self):
        get_layer_ids(self.layer, use_cache=False)
        self.layer.refresh_from_db()
        self.assertIsNotNone(self.layer.last_evaluation_ms)
        self.assertIsNotNone(self.layer.last_evaluated)

    def test_bbox_evaluation_does_not_change_the_figures(self):
        get_layer_ids(self.layer, bbox=(-180, -90, 180, 90), use_cache=False)
        self.layer.refresh_from_db()
        self.assertIsNone(self.layer.last_evaluation_ms)

    def test_a_timeout_is_counted_as_a_failure(self):
        with mock.patch.object(
            ogc_layer_utils, 'get_matched_queryset',
            side_effect=OgcLayerTimeoutError('slow')
        ):
            with self.assertRaises(OgcLayerTimeoutError):
                get_layer_ids(self.layer, use_cache=False)
        self.layer.refresh_from_db()
        self.assertEqual(self.layer.failure_count, 1)

    def test_extent_timeout_is_counted_as_a_failure(self):
        with mock.patch.object(
            ogc_layer_utils, '_compute_extent',
            side_effect=OgcLayerTimeoutError('slow')
        ):
            with self.assertRaises(OgcLayerTimeoutError):
                get_layer_extent(self.layer, use_cache=False)
        self.layer.refresh_from_db()
        self.assertEqual(self.layer.failure_count, 1)

    def test_over_cap_counts_as_a_successful_search(self):
        self.layer.record_failure()
        with self.settings(OGC_LAYER_MAX_RECORDS=0):
            with self.assertRaises(ogc_layer_utils.OgcLayerOverCapError):
                get_layer_ids(self.layer, use_cache=False)
        self.layer.refresh_from_db()
        self.assertEqual(self.layer.failure_count, 0)

    def test_repeated_timeouts_switch_the_layer_off_for_clients(self):
        with mock.patch.object(
            ogc_layer_utils, 'get_matched_queryset',
            side_effect=OgcLayerTimeoutError('slow')
        ):
            codes = [self.items().status_code for _ in range(3)]
        self.assertEqual(codes, [503, 503, 503])
        self.assertEqual(self.items().status_code, 404)
        self.layer.refresh_from_db()
        self.assertFalse(self.layer.is_active)

    def test_a_good_evaluation_between_timeouts_keeps_the_layer_on(self):
        failing = mock.patch.object(
            ogc_layer_utils, 'get_matched_queryset',
            side_effect=OgcLayerTimeoutError('slow'))
        with failing:
            self.items()
            self.items()
        cache.clear()
        self.assertEqual(self.items().status_code, 200)
        cache.clear()
        with failing:
            self.items()
            self.items()
        self.layer.refresh_from_db()
        self.assertTrue(self.layer.is_active)


class TestOwnerLimit(CostControlTestCase):

    def test_creating_over_the_limit_is_refused(self):
        with self.settings(OGC_MAX_LAYERS_PER_OWNER=2):
            self.create_layer()
            with self.assertRaises(ValidationError) as raised:
                OgcLayer(name='Third', owner=self.owner).clean()
        self.assertIn('owner', raised.exception.message_dict)

    def test_under_the_limit_is_fine(self):
        with self.settings(OGC_MAX_LAYERS_PER_OWNER=3):
            self.create_layer()
            OgcLayer(name='Third', owner=self.owner).clean()

    def test_revoked_layers_do_not_count(self):
        with self.settings(OGC_MAX_LAYERS_PER_OWNER=1):
            self.layer.is_active = False
            self.layer.save()
            OgcLayer(name='New', owner=self.owner).clean()

    def test_existing_layers_can_still_be_edited(self):
        with self.settings(OGC_MAX_LAYERS_PER_OWNER=1):
            self.layer.name = 'Renamed'
            self.layer.clean()

    def test_other_owners_are_not_affected(self):
        other = UserF.create(username='cost_other')
        with self.settings(OGC_MAX_LAYERS_PER_OWNER=1):
            OgcLayer(name='Theirs', owner=other).clean()

    def test_zero_means_no_limit(self):
        with self.settings(OGC_MAX_LAYERS_PER_OWNER=0):
            for _ in range(3):
                self.create_layer()
            OgcLayer(name='More', owner=self.owner).clean()


class TestKillSwitch(CostControlTestCase):

    def test_every_endpoint_answers_503_when_switched_off(self):
        token = self.layer.raw_token
        urls = [
            reverse('ogc-landing-page', kwargs={'token': token}),
            reverse('ogc-conformance', kwargs={'token': token}),
            reverse('ogc-api', kwargs={'token': token}),
            reverse('ogc-collections', kwargs={'token': token}),
            reverse('ogc-items', kwargs={
                'token': token, 'collection_id': 'records'}),
        ]
        with self.settings(OGC_LAYERS_ENABLED=False, OGC_LAYER_RETRY_AFTER=42):
            for url in urls:
                response = self.client.get(url)
                self.assertEqual(response.status_code, 503, url)
                self.assertEqual(response['Retry-After'], '42')
                self.assertEqual(
                    response.json()['code'], 'ServiceUnavailable')

    def test_switched_off_layers_are_not_read_or_touched(self):
        with self.settings(OGC_LAYERS_ENABLED=False):
            with mock.patch.object(
                OgcLayer, 'get_by_token',
                side_effect=AssertionError('no lookup when switched off')
            ):
                response = self.items()
        self.assertEqual(response.status_code, 503)
        self.layer.refresh_from_db()
        self.assertIsNone(self.layer.last_accessed)

    def test_layers_work_again_when_switched_on(self):
        with self.settings(OGC_LAYERS_ENABLED=False):
            self.items()
        self.assertEqual(self.items().status_code, 200)


class TestSlowRequestLog(CostControlTestCase):

    def test_slow_request_is_logged_without_the_token(self):
        with self.settings(OGC_SLOW_REQUEST_SECONDS=0.000001):
            with self.assertLogs(
                'bims.api_views.ogc_features', level='WARNING'
            ) as logs:
                self.items(limit=7, offset=3)
        message = '\n'.join(logs.output)
        self.assertIn('Slow OGC request', message)
        self.assertIn('layer=%s' % self.layer.pk, message)
        self.assertIn('ItemsView', message)
        self.assertIn("'limit': '7'", message)
        self.assertNotIn(self.layer.raw_token, message)

    def test_fast_requests_are_not_logged(self):
        with self.assertNoLogs('bims.api_views.ogc_features', level='WARNING'):
            self.items()

    def test_zero_disables_the_log(self):
        with self.settings(OGC_SLOW_REQUEST_SECONDS=0):
            with self.assertNoLogs(
                'bims.api_views.ogc_features', level='WARNING'
            ):
                self.items()

    def test_slow_failed_request_is_logged_with_its_status(self):
        with self.settings(OGC_SLOW_REQUEST_SECONDS=0.000001):
            with self.assertLogs(
                'bims.api_views.ogc_features', level='WARNING'
            ) as logs:
                self.items(limit='abc')
        self.assertIn('status=400', '\n'.join(logs.output))


class TestRequestCount(CostControlTestCase):

    def test_first_request_is_counted(self):
        self.items()
        self.layer.refresh_from_db()
        self.assertEqual(self.layer.request_count, 1)

    def test_requests_are_written_every_few_minutes(self):
        self.items()
        for _ in range(3):
            self.items()
        self.layer.refresh_from_db()
        # Only the first request has been written, the rest wait in the cache
        self.assertEqual(self.layer.request_count, 1)
        OgcLayer.objects.filter(pk=self.layer.pk).update(
            last_accessed=timezone.now() - timedelta(minutes=10))
        self.items()
        self.layer.refresh_from_db()
        self.assertEqual(self.layer.request_count, 5)

    def test_requests_are_counted_without_a_cache(self):
        dummy = {'default': {
            'BACKEND': 'django.core.cache.backends.dummy.DummyCache'}}
        with self.settings(CACHES=dummy):
            self.items()
        self.layer.refresh_from_db()
        self.assertEqual(self.layer.request_count, 1)


class TestCostAdmin(CostControlTestCase):

    def setUp(self):
        super().setUp()
        self.model_admin = OgcLayerAdmin(OgcLayer, AdminSite())
        self.model_admin.message_user = mock.Mock()
        self.request = RequestFactory().post('/')
        self.request.user = self.owner

    def test_figures_are_shown_and_read_only(self):
        for name in (
            'last_evaluation_ms', 'request_count', 'failure_count'
        ):
            self.assertIn(name, self.model_admin.list_display)
            self.assertIn(name, self.model_admin.readonly_fields)
        self.assertIn('disabled_reason', self.model_admin.readonly_fields)

    def test_reactivate_switches_a_layer_back_on(self):
        for _ in range(3):
            self.layer.record_failure()
        self.model_admin.reactivate(self.request, OgcLayer.objects.all())
        self.layer.refresh_from_db()
        self.assertTrue(self.layer.is_active)
        self.assertEqual(self.layer.failure_count, 0)
        self.assertEqual(self.layer.disabled_reason, '')
        self.assertEqual(self.items().status_code, 200)

    def test_switching_on_by_hand_clears_the_failures(self):
        for _ in range(3):
            self.layer.record_failure()
        self.layer.refresh_from_db()
        self.layer.is_active = True
        form = mock.Mock(changed_data=['is_active'])
        self.model_admin.save_model(self.request, self.layer, form, True)
        self.layer.refresh_from_db()
        self.assertEqual(self.layer.failure_count, 0)
        self.assertEqual(self.layer.disabled_reason, '')

    def test_other_edits_keep_the_failure_state(self):
        self.layer.record_failure()
        self.layer.refresh_from_db()
        form = mock.Mock(changed_data=['name'])
        self.model_admin.save_model(self.request, self.layer, form, True)
        self.layer.refresh_from_db()
        self.assertEqual(self.layer.failure_count, 1)

    def test_action_is_registered(self):
        self.assertIn('reactivate', self.model_admin.actions)
