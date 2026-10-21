# coding=utf-8
from datetime import timedelta

from django.contrib.auth.models import Group
from django.core.cache import cache
from django.test import TestCase, override_settings
from django.utils import timezone

from bims.models import OgcLayer
from bims.tests.model_factories import (
    BiologicalCollectionRecordF,
    LocationSiteF,
    TaxonomyF,
    UserF,
)
from bims.models.biological_collection_record import (
    BiologicalCollectionRecord
)
from bims.utils.ogc_layer import (
    OgcLayerFilterError,
    OgcLayerOverCapError,
    count_layer_records,
    get_layer_extent,
    get_layer_ids,
    get_matched_queryset,
    has_narrowing_filter,
    validate_layer,
    validate_query,
    visible_records,
    _decode_ids,
    _encode_ids,
)


class TestNarrowingFilter(TestCase):

    def test_empty_queries_are_not_narrowing(self):
        for query in (None, [], 'text', {}, {'validated': '["validated"]'},
                      {'taxon': ''}, {'search': '  '}, {'siteId': '[]'},
                      {'yearFrom': '2010'}, {'yearTo': '2020'},
                      {'unknown': 'x'}):
            self.assertFalse(has_narrowing_filter(query), query)

    def test_narrowing_queries(self):
        for query in ({'taxon': '1'}, {'search': 'fish'},
                      {'siteId': '1,2'}, {'reference': '[3]'},
                      {'yearFrom': '2010', 'yearTo': '2020'},
                      {'polygon': '[[[0,0],[1,1],[1,0],[0,0]]]'}):
            self.assertTrue(has_narrowing_filter(query), query)

    def test_validate_query_rejects_empty(self):
        with self.assertRaises(OgcLayerFilterError):
            validate_query({})
        with self.assertRaises(OgcLayerFilterError):
            validate_query('text')

    def test_validate_query_rejects_other_modules(self):
        for module in ('water_temperature', 'physico_chemistry', 'climate'):
            with self.assertRaises(OgcLayerFilterError):
                validate_query({'taxon': '1', 'module': module})
        with self.assertRaises(OgcLayerFilterError):
            validate_query({'taxon': '1', 'thermalModule': 'True'})

    def test_validate_query_accepts_narrowing(self):
        validate_query({'taxon': '1'})


class OgcLayerServiceTestCase(TestCase):

    def setUp(self):
        cache.clear()
        self.owner = UserF.create(username='layer_owner')
        self.taxon = TaxonomyF.create()
        self.other_taxon = TaxonomyF.create()
        self.site = LocationSiteF.create()

    def create_record(self, **kwargs):
        kwargs.setdefault('taxonomy', self.taxon)
        kwargs.setdefault('site', self.site)
        return BiologicalCollectionRecordF.create(**kwargs)

    def create_layer(self, query=None, **kwargs):
        if query is None:
            query = {'taxon': str(self.taxon.id)}
        return OgcLayer.objects.create(
            name='Layer', owner=self.owner, query=query, **kwargs)

    def ids(self, layer):
        return get_layer_ids(layer, use_cache=False)


class TestLayerFilter(OgcLayerServiceTestCase):

    def test_returns_records_matching_filter(self):
        match = self.create_record()
        self.create_record(taxonomy=self.other_taxon)
        self.assertEqual(self.ids(self.create_layer()), [match.id])

    def test_matches_collection_search(self):
        from bims.api_views.search import CollectionSearch
        self.create_record()
        self.create_record()
        self.create_record(taxonomy=self.other_taxon)
        layer = self.create_layer()
        expected = CollectionSearch(
            layer.query, requester_id=self.owner.id
        ).process_search().filter(validated=True)
        self.assertEqual(
            set(self.ids(layer)),
            set(expected.values_list('id', flat=True)))

    def test_ordered_by_id(self):
        records = [self.create_record() for _ in range(3)]
        self.assertEqual(
            self.ids(self.create_layer()), sorted(r.id for r in records))

    def test_empty_filter_is_rejected(self):
        with self.assertRaises(OgcLayerFilterError):
            get_matched_queryset(self.create_layer(query={}))

    def test_sass_filter_is_rejected(self):
        layer = self.create_layer(query={
            'taxon': str(self.taxon.id),
            'validated': '["sass accredited"]'})
        with self.assertRaises(OgcLayerFilterError):
            get_matched_queryset(layer)

    def test_unvalidated_records_are_excluded(self):
        self.create_record(validated=False)
        visible = self.create_record()
        self.assertEqual(self.ids(self.create_layer()), [visible.id])

    def test_client_cannot_override_requester(self):
        other = UserF.create(username='someone_else')
        embargoed = self.create_record(
            owner=other,
            end_embargo_date=timezone.now().date() + timedelta(days=30))
        layer = self.create_layer(query={
            'taxon': str(self.taxon.id), 'requester': str(other.id)})
        self.assertNotIn(embargoed.id, self.ids(layer))

    def test_inactive_owner_gets_nothing(self):
        self.create_record()
        layer = self.create_layer()
        self.owner.is_active = False
        self.owner.save()
        layer.refresh_from_db()
        self.assertEqual(self.ids(layer), [])

    def test_no_duplicates_from_joins(self):
        record = self.create_record()
        self.assertEqual(
            self.ids(self.create_layer(query={
                'taxon': str(self.taxon.id),
                'siteId': str(self.site.id)})),
            [record.id])


class TestEmbargo(OgcLayerServiceTestCase):

    def test_owner_embargoed_record_is_not_served(self):
        record = self.create_record(
            owner=self.owner,
            end_embargo_date=timezone.now().date() + timedelta(days=30))
        self.assertNotIn(record.id, self.ids(self.create_layer()))

    def test_expired_embargo_is_served(self):
        record = self.create_record(
            end_embargo_date=timezone.now().date() - timedelta(days=1))
        self.assertIn(record.id, self.ids(self.create_layer()))

    def test_embargo_not_started_is_served(self):
        record = self.create_record(
            start_embargo_date=timezone.now().date() + timedelta(days=5),
            end_embargo_date=timezone.now().date() + timedelta(days=30))
        self.assertIn(record.id, self.ids(self.create_layer()))


class TestDataTypes(OgcLayerServiceTestCase):

    def setUp(self):
        super().setUp()
        self.public = self.create_record(data_type='public')
        self.untyped = self.create_record(data_type='')
        self.sensitive = self.create_record(data_type='sensitive')
        self.private = self.create_record(data_type='private')

    def add_group(self, name):
        group, _ = Group.objects.get_or_create(name=name)
        self.owner.groups.add(group)

    def test_public_only_by_default(self):
        self.add_group('SensitiveDataGroup')
        self.add_group('PrivateDataGroup')
        self.assertEqual(
            set(self.ids(self.create_layer())),
            {self.public.id, self.untyped.id})

    def test_sensitive_needs_flag_and_group(self):
        layer = self.create_layer(include_sensitive=True)
        self.assertNotIn(self.sensitive.id, self.ids(layer))
        self.add_group('SensitiveDataGroup')
        layer = OgcLayer.objects.get(pk=layer.pk)
        self.assertIn(self.sensitive.id, self.ids(layer))
        self.assertNotIn(self.private.id, self.ids(layer))

    def test_group_without_flag_is_not_enough(self):
        self.add_group('SensitiveDataGroup')
        self.assertNotIn(
            self.sensitive.id, self.ids(self.create_layer()))

    def test_private_needs_flag_and_group(self):
        layer = self.create_layer(include_private=True)
        self.assertNotIn(self.private.id, self.ids(layer))
        self.add_group('PrivateDataGroup')
        layer = OgcLayer.objects.get(pk=layer.pk)
        self.assertIn(self.private.id, self.ids(layer))
        self.assertNotIn(self.sensitive.id, self.ids(layer))


class TestCountLayerRecords(OgcLayerServiceTestCase):

    def test_counts_records(self):
        for _ in range(3):
            self.create_record()
        self.assertEqual(count_layer_records(self.create_layer()), 3)

    def test_zero_records(self):
        self.assertEqual(count_layer_records(self.create_layer()), 0)

    @override_settings(OGC_LAYER_MAX_RECORDS=3)
    def test_at_cap_is_allowed(self):
        for _ in range(3):
            self.create_record()
        self.assertEqual(count_layer_records(self.create_layer()), 3)

    @override_settings(OGC_LAYER_MAX_RECORDS=3)
    def test_over_cap_raises(self):
        for _ in range(4):
            self.create_record()
        with self.assertRaises(OgcLayerOverCapError) as ctx:
            count_layer_records(self.create_layer())
        self.assertEqual(ctx.exception.cap, 3)
        self.assertIn('3', str(ctx.exception))

    @override_settings(OGC_LAYER_MAX_RECORDS=3)
    def test_layer_that_grows_past_cap_raises(self):
        for _ in range(3):
            self.create_record()
        layer = self.create_layer()
        self.assertEqual(count_layer_records(layer, use_cache=False), 3)
        self.create_record()
        with self.assertRaises(OgcLayerOverCapError):
            count_layer_records(layer, use_cache=False)

    @override_settings(OGC_LAYER_MAX_RECORDS=3)
    def test_over_cap_result_is_cached(self):
        for _ in range(4):
            self.create_record()
        layer = self.create_layer()
        for _ in range(2):
            with self.assertRaises(OgcLayerOverCapError):
                count_layer_records(layer)

    def test_count_is_cached(self):
        self.create_record()
        layer = self.create_layer()
        self.assertEqual(count_layer_records(layer), 1)
        self.create_record()
        self.assertEqual(count_layer_records(layer), 1)
        self.assertEqual(count_layer_records(layer, use_cache=False), 2)

    def test_cache_is_per_filter(self):
        self.create_record()
        self.create_record(taxonomy=self.other_taxon)
        self.create_record(taxonomy=self.other_taxon)
        layer = self.create_layer()
        self.assertEqual(count_layer_records(layer), 1)
        layer.query = {'taxon': str(self.other_taxon.id)}
        layer.save()
        self.assertEqual(count_layer_records(layer), 2)

    def test_count_saved_on_layer(self):
        self.create_record()
        self.create_record()
        layer = self.create_layer()
        count_layer_records(layer)
        layer.refresh_from_db()
        self.assertEqual(layer.record_count_cached, 2)
        self.assertIsNotNone(layer.record_count_updated)

    @override_settings(OGC_LAYER_MAX_RECORDS=1)
    def test_over_cap_does_not_overwrite_saved_count(self):
        self.create_record()
        layer = self.create_layer()
        count_layer_records(layer)
        self.create_record()
        with self.assertRaises(OgcLayerOverCapError):
            count_layer_records(layer, use_cache=False)
        layer.refresh_from_db()
        self.assertEqual(layer.record_count_cached, 1)


class TestValidateLayer(OgcLayerServiceTestCase):

    def test_returns_count(self):
        self.create_record()
        self.assertEqual(validate_layer(self.create_layer()), 1)

    def test_rejects_empty_filter(self):
        with self.assertRaises(OgcLayerFilterError):
            validate_layer(self.create_layer(query={}))

    @override_settings(OGC_LAYER_MAX_RECORDS=1)
    def test_rejects_over_cap(self):
        self.create_record()
        self.create_record()
        with self.assertRaises(OgcLayerOverCapError):
            validate_layer(self.create_layer())

    def test_ignores_stale_cache(self):
        layer = self.create_layer()
        self.assertEqual(validate_layer(layer), 0)
        self.create_record()
        self.assertEqual(validate_layer(layer), 1)


class TestCreateLayerFromSearchProcess(OgcLayerServiceTestCase):

    def setUp(self):
        from unittest import mock
        from django.contrib.admin.sites import AdminSite
        from django.test import RequestFactory
        from bims.admin import SearchProcessAdmin
        from bims.models import SearchProcess

        super().setUp()
        self.SearchProcess = SearchProcess
        self.model_admin = SearchProcessAdmin(SearchProcess, AdminSite())
        self.model_admin.message_user = mock.Mock()
        self.request = RequestFactory().post('/')
        self.request.user = UserF.create(username='admin_user')
        self.create_record()

    def create_process(self, query=None, **kwargs):
        if query is None:
            query = (
                'http://fbis.local/api/collection-search/?taxon=%d'
                '&requester=%d' % (self.taxon.id, self.owner.id))
        kwargs.setdefault('category', 'search_results')
        kwargs.setdefault('finished', True)
        return self.SearchProcess.objects.create(query=query, **kwargs)

    def run_action(self):
        self.model_admin.create_ogc_layer(
            self.request, self.SearchProcess.objects.all())

    def messages(self):
        return [call.args[1] for call in
                self.model_admin.message_user.call_args_list]

    def test_creates_layer_from_finished_search(self):
        self.create_process(requester=self.owner)
        self.run_action()
        layer = OgcLayer.objects.get()
        self.assertEqual(layer.owner, self.owner)
        self.assertEqual(layer.query, {'taxon': str(self.taxon.id)})
        self.assertIn(layer.token_hint, self.messages()[-1])

    def test_unfinished_search_is_skipped(self):
        self.create_process(finished=False)
        self.run_action()
        self.assertFalse(OgcLayer.objects.exists())
        self.assertIn('not finished', self.messages()[0])

    def test_other_category_is_skipped(self):
        self.create_process(category='cluster_generation')
        self.run_action()
        self.assertFalse(OgcLayer.objects.exists())

    def test_falls_back_to_current_user(self):
        self.create_process()
        self.run_action()
        self.assertEqual(OgcLayer.objects.get().owner, self.request.user)

    def test_relative_query_string_is_parsed(self):
        self.create_process(query='/api/?taxon=%d' % self.taxon.id)
        self.run_action()
        self.assertEqual(
            OgcLayer.objects.get().query, {'taxon': str(self.taxon.id)})

    def test_search_without_filter_reports_error(self):
        self.create_process(query='http://fbis.local/api/?validated=1')
        self.run_action()
        self.assertFalse(OgcLayer.objects.exists())
        self.assertIn('at least one filter', self.messages()[-1])

    @override_settings(OGC_LAYER_MAX_RECORDS=1)
    def test_over_cap_reports_error(self):
        self.create_record()
        self.create_process()
        self.run_action()
        self.assertFalse(OgcLayer.objects.exists())
        self.assertIn('more than 1', self.messages()[-1])


class TestGetLayerIds(OgcLayerServiceTestCase):

    def test_ids_are_sorted_and_match_queryset(self):
        records = [self.create_record() for _ in range(3)]
        records.append(self.create_record(taxonomy=self.other_taxon))
        layer = self.create_layer()
        ids = get_layer_ids(layer)
        self.assertEqual(ids, sorted(ids))
        self.assertEqual(ids, self.ids(layer))
        self.assertEqual(len(ids), 3)

    def test_ids_are_cached(self):
        self.create_record()
        layer = self.create_layer()
        first = get_layer_ids(layer)
        self.create_record()
        self.assertEqual(get_layer_ids(layer), first)
        self.assertEqual(len(get_layer_ids(layer, use_cache=False)), 2)

    def test_encode_round_trip(self):
        ids = [1, 2, 5, 4294967296, 90000000000]
        self.assertEqual(_decode_ids(_encode_ids(ids)), ids)
        self.assertEqual(_decode_ids(_encode_ids([])), [])

    def test_cache_failure_is_tolerated(self):
        from unittest import mock
        self.create_record()
        layer = self.create_layer()
        with mock.patch(
            'bims.utils.ogc_layer.cache.set',
            side_effect=Exception('too large')
        ):
            self.assertEqual(len(get_layer_ids(layer)), 1)

    @override_settings(OGC_LAYER_MAX_RECORDS=2)
    def test_reads_at_most_one_past_the_cap(self):
        for _ in range(5):
            self.create_record()
        layer = self.create_layer()
        with self.assertRaises(OgcLayerOverCapError):
            get_layer_ids(layer)
        # The over-cap result is cached too
        with self.assertNumQueries(0):
            with self.assertRaises(OgcLayerOverCapError):
                get_layer_ids(layer)

    def test_bbox_restricts_ids(self):
        from django.contrib.gis.geos import Point
        inside_site = LocationSiteF.create(geometry_point=Point(10.0, 10.0))
        outside_site = LocationSiteF.create(
            geometry_point=Point(-80.0, -80.0))
        inside = self.create_record(site=inside_site)
        self.create_record(site=outside_site)
        layer = self.create_layer()
        self.assertEqual(len(get_layer_ids(layer)), 2)
        self.assertEqual(
            get_layer_ids(layer, bbox=(0, 0, 20, 20)), [inside.id])
        self.assertEqual(get_layer_ids(layer, bbox=(50, 50, 60, 60)), [])

    def test_bbox_ids_cached_separately(self):
        from django.contrib.gis.geos import Point
        site = LocationSiteF.create(geometry_point=Point(10.0, 10.0))
        self.create_record(site=site)
        layer = self.create_layer()
        self.assertEqual(len(get_layer_ids(layer, bbox=(0, 0, 20, 20))), 1)
        self.assertEqual(get_layer_ids(layer, bbox=(50, 50, 60, 60)), [])

    def test_does_not_update_saved_count_for_bbox(self):
        self.create_record()
        layer = self.create_layer()
        get_layer_ids(layer, bbox=(50, 50, 60, 60))
        layer.refresh_from_db()
        self.assertIsNone(layer.record_count_cached)


class TestVisibleRecords(OgcLayerServiceTestCase):

    def test_cached_id_is_not_served_after_embargo(self):
        record = self.create_record()
        layer = self.create_layer()
        ids = get_layer_ids(layer)
        self.assertEqual(ids, [record.id])
        BiologicalCollectionRecord.objects.filter(pk=record.pk).update(
            end_embargo_date=timezone.now().date() + timedelta(days=10))
        page = visible_records(
            BiologicalCollectionRecord.objects.filter(pk__in=ids), layer)
        self.assertEqual(list(page), [])

    def test_cached_id_is_not_served_after_unvalidated(self):
        record = self.create_record()
        layer = self.create_layer()
        ids = get_layer_ids(layer)
        BiologicalCollectionRecord.objects.filter(pk=record.pk).update(
            validated=False)
        page = visible_records(
            BiologicalCollectionRecord.objects.filter(pk__in=ids), layer)
        self.assertEqual(list(page), [])

    def test_cached_id_is_not_served_after_data_type_change(self):
        record = self.create_record()
        layer = self.create_layer()
        ids = get_layer_ids(layer)
        BiologicalCollectionRecord.objects.filter(pk=record.pk).update(
            data_type='private')
        page = visible_records(
            BiologicalCollectionRecord.objects.filter(pk__in=ids), layer)
        self.assertEqual(list(page), [])


class TestGetLayerExtent(OgcLayerServiceTestCase):

    def test_extent_of_points(self):
        from django.contrib.gis.geos import Point
        self.create_record(site=LocationSiteF.create(
            geometry_point=Point(10.0, 20.0)))
        self.create_record(site=LocationSiteF.create(
            geometry_point=Point(-5.0, 30.0)))
        self.assertEqual(
            get_layer_extent(self.create_layer()), [-5.0, 20.0, 10.0, 30.0])

    def test_extent_ignores_records_outside_the_filter(self):
        from django.contrib.gis.geos import Point
        self.create_record(site=LocationSiteF.create(
            geometry_point=Point(10.0, 20.0)))
        self.create_record(
            taxonomy=self.other_taxon,
            site=LocationSiteF.create(geometry_point=Point(80.0, 60.0)))
        self.assertEqual(
            get_layer_extent(self.create_layer()), [10.0, 20.0, 10.0, 20.0])

    def test_no_records_has_no_extent(self):
        self.assertIsNone(get_layer_extent(self.create_layer()))

    def test_extent_is_cached(self):
        from django.contrib.gis.geos import Point
        self.create_record(site=LocationSiteF.create(
            geometry_point=Point(10.0, 20.0)))
        layer = self.create_layer()
        first = get_layer_extent(layer)
        self.create_record(site=LocationSiteF.create(
            geometry_point=Point(50.0, 50.0)))
        self.assertEqual(get_layer_extent(layer), first)
        self.assertNotEqual(get_layer_extent(layer, use_cache=False), first)

    @override_settings(OGC_LAYER_MAX_RECORDS=1)
    def test_over_cap_raises(self):
        self.create_record()
        self.create_record()
        with self.assertRaises(OgcLayerOverCapError):
            get_layer_extent(self.create_layer())
