from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse
from django_tenants.test.cases import FastTenantTestCase
from django_tenants.test.client import TenantClient

from bims.models.search_process import (
    SearchProcess,
    SPATIAL_DASHBOARD_CONS_STATUS,
    SPATIAL_DASHBOARD_RLI,
    SPATIAL_DASHBOARD_MAP,
    SPATIAL_DASHBOARD_SUMMARY,
)
from bims.tests.model_factories import (
    BiologicalCollectionRecordF,
    LocationSiteF,
    TaxonomyF,
    TaxonGroupF,
    IUCNStatusF,
    EndemismF,
    UserF,
)


class TestSpatialDashboardView(FastTenantTestCase):
    """Tests for the spatial dashboard template view."""

    def setUp(self):
        self.client = TenantClient(self.tenant)
        self.user = UserF.create()
        self.url = reverse('spatial-dashboard')

    def test_requires_login(self):
        response = self.client.get(self.url)
        self.assertNotEqual(response.status_code, 200)

    def test_accessible_when_logged_in(self):
        self.client.login(
            username=self.user.username,
            password='password',
        )
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_template_used(self):
        self.client.login(
            username=self.user.username,
            password='password',
        )
        response = self.client.get(self.url)
        self.assertTemplateUsed(response, 'spatial_dashboard.html')

    def test_context_has_basemap_layers(self):
        self.client.login(
            username=self.user.username,
            password='password',
        )
        response = self.client.get(self.url)
        self.assertIn('basemap_layers', response.context)


class TestSpatialDashboardApis(FastTenantTestCase):
    """Tests for the spatial dashboard API endpoints."""

    def setUp(self):
        self.client = TenantClient(self.tenant)
        self.user = UserF.create()

        self.module = TaxonGroupF.create(
            name='Fish',
            category='SPECIES_MODULE',
            display_order=0,
        )

        endemism = EndemismF.create(name='Endemic')
        endemism_2 = EndemismF.create(name='Non-endemic')

        iucn_lc = IUCNStatusF.create(category='LC', national=False)
        iucn_vu = IUCNStatusF.create(category='VU', national=False)

        self.taxa_1 = TaxonomyF.create(
            scientific_name='Species A',
            origin='Native',
            iucn_status=iucn_lc,
            endemism=endemism,
        )
        self.taxa_2 = TaxonomyF.create(
            scientific_name='Species B',
            origin='Non-native',
            iucn_status=iucn_vu,
            endemism=endemism_2,
        )

        site = LocationSiteF.create()
        BiologicalCollectionRecordF.create(
            taxonomy=self.taxa_1,
            collection_date='2020-06-15',
            site=site,
            module_group=self.module,
            validated=True,
        )
        BiologicalCollectionRecordF.create(
            taxonomy=self.taxa_2,
            collection_date='2021-03-10',
            site=site,
            module_group=self.module,
            validated=True,
        )

    def test_apis_require_login(self):
        urls = [
            reverse('spatial-dashboard-cons-status'),
            reverse('spatial-dashboard-rli'),
            reverse('spatial-dashboard-map'),
            reverse('spatial-dashboard-summary'),
        ]
        for url in urls:
            response = self.client.get(url)
            self.assertNotEqual(
                response.status_code, 200,
                f'{url} should require login',
            )

    @patch('bims.api_views.spatial_dashboard.spatial_dashboard_cons_status.delay')
    def test_cons_status_api_triggers_task(self, mock_delay):
        mock_delay.return_value.id = 'fake-task-id'
        self.client.login(
            username=self.user.username,
            password='password',
        )
        url = reverse('spatial-dashboard-cons-status')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        mock_delay.assert_called_once()

    @patch('bims.api_views.spatial_dashboard.spatial_dashboard_rli.delay')
    def test_rli_api_triggers_task(self, mock_delay):
        mock_delay.return_value.id = 'fake-task-id'
        self.client.login(
            username=self.user.username,
            password='password',
        )
        url = reverse('spatial-dashboard-rli')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        mock_delay.assert_called_once()

    @patch('bims.api_views.spatial_dashboard.spatial_dashboard_map.delay')
    def test_map_api_triggers_task(self, mock_delay):
        mock_delay.return_value.id = 'fake-task-id'
        self.client.login(
            username=self.user.username,
            password='password',
        )
        url = reverse('spatial-dashboard-map')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        mock_delay.assert_called_once()

    @patch('bims.api_views.spatial_dashboard.spatial_dashboard_summary.delay')
    def test_summary_api_triggers_task(self, mock_delay):
        mock_delay.return_value.id = 'fake-task-id'
        self.client.login(
            username=self.user.username,
            password='password',
        )
        url = reverse('spatial-dashboard-summary')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        mock_delay.assert_called_once()

    @patch('bims.api_views.spatial_dashboard.spatial_dashboard_cons_status.delay')
    def test_cons_status_returns_processing(self, mock_delay):
        mock_delay.return_value.id = 'fake-task-id'
        self.client.login(
            username=self.user.username,
            password='password',
        )
        url = reverse('spatial-dashboard-cons-status')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertIn('status', response.data)
        self.assertEqual(response.data['status'], 'processing')

class TestSpatialDashboardTasks(FastTenantTestCase):
    """Tests for the spatial dashboard Celery tasks."""

    def setUp(self):
        self.user = UserF.create()
        self.module = TaxonGroupF.create(
            name='Fish',
            category='SPECIES_MODULE',
            display_order=0,
        )
        endemism = EndemismF.create(name='Endemic')
        iucn_lc = IUCNStatusF.create(category='LC', national=False)
        iucn_vu = IUCNStatusF.create(category='VU', national=False)

        self.taxa_1 = TaxonomyF.create(
            scientific_name='Species A',
            canonical_name='Species A',
            origin='Native',
            iucn_status=iucn_lc,
            endemism=endemism,
        )
        self.taxa_2 = TaxonomyF.create(
            scientific_name='Species B',
            canonical_name='Species B',
            origin='Non-native',
            iucn_status=iucn_vu,
            endemism=endemism,
        )

        site = LocationSiteF.create()
        BiologicalCollectionRecordF.create(
            taxonomy=self.taxa_1,
            original_species_name='test_species_1',
            collection_date='2020-06-15',
            site=site,
            module_group=self.module,
            validated=True,
        )
        BiologicalCollectionRecordF.create(
            taxonomy=self.taxa_2,
            original_species_name='test_species_2',
            collection_date='2021-03-10',
            site=site,
            module_group=self.module,
            validated=True,
        )

        self.search_params = {
            'search': 'Species',
            'requester': str(self.user.id),
        }

    def _create_search_process(self, category):
        sp = SearchProcess.objects.create(
            category=category,
            requester=self.user,
        )
        sp.set_process_id('test-process-id')
        return sp

    @patch('bims.utils.celery.memcache_lock')
    def test_cons_status_task(self, mock_lock):
        from bims.tasks.spatial_dashboard import spatial_dashboard_cons_status

        mock_lock.return_value.__enter__ = lambda s: True
        mock_lock.return_value.__exit__ = lambda s, *a: None

        search_process = self._create_search_process(
            SPATIAL_DASHBOARD_CONS_STATUS
        )
        spatial_dashboard_cons_status(
            search_parameters=self.search_params,
            search_process_id=search_process.id,
        )
        search_process.refresh_from_db()
        self.assertTrue(search_process.finished)
        results = search_process.get_file_if_exits()
        self.assertIsNotNone(results)
        self.assertIn('modules', results)

    @patch('bims.utils.celery.memcache_lock')
    def test_rli_task(self, mock_lock):
        from bims.tasks.spatial_dashboard import spatial_dashboard_rli

        mock_lock.return_value.__enter__ = lambda s: True
        mock_lock.return_value.__exit__ = lambda s, *a: None

        search_process = self._create_search_process(
            SPATIAL_DASHBOARD_RLI
        )
        spatial_dashboard_rli(
            search_parameters=self.search_params,
            search_process_id=search_process.id,
        )
        search_process.refresh_from_db()
        self.assertTrue(search_process.finished)
        results = search_process.get_file_if_exits()
        self.assertIsNotNone(results)
        self.assertIn('series', results)
        self.assertIn('aggregate', results)

    @patch('bims.utils.celery.memcache_lock')
    def test_rli_task_values(self, mock_lock):
        from bims.tasks.spatial_dashboard import spatial_dashboard_rli

        mock_lock.return_value.__enter__ = lambda s: True
        mock_lock.return_value.__exit__ = lambda s, *a: None

        search_process = self._create_search_process(
            SPATIAL_DASHBOARD_RLI
        )
        spatial_dashboard_rli(
            search_parameters=self.search_params,
            search_process_id=search_process.id,
        )
        search_process.refresh_from_db()
        results = search_process.get_file_if_exits()
        # Aggregate should have entries for 2020 and 2021
        aggregate = results['aggregate']
        years = [p['year'] for p in aggregate]
        self.assertIn(2020, years)
        self.assertIn(2021, years)
        # LC weight=0 so RLI for 2020 should be 1.0
        year_2020 = next(p for p in aggregate if p['year'] == 2020)
        self.assertEqual(year_2020['value'], 1.0)
        # VU weight=2 so RLI for 2021 should be 1 - (2/(1*5)) = 0.6
        year_2021 = next(p for p in aggregate if p['year'] == 2021)
        self.assertEqual(year_2021['value'], 0.6)

    @patch('bims.utils.celery.memcache_lock')
    def test_summary_task(self, mock_lock):
        from bims.tasks.spatial_dashboard import spatial_dashboard_summary

        mock_lock.return_value.__enter__ = lambda s: True
        mock_lock.return_value.__exit__ = lambda s, *a: None

        search_process = self._create_search_process(
            SPATIAL_DASHBOARD_SUMMARY
        )
        spatial_dashboard_summary(
            search_parameters=self.search_params,
            search_process_id=search_process.id,
        )
        search_process.refresh_from_db()
        self.assertTrue(search_process.finished)
        results = search_process.get_file_if_exits()
        self.assertIsNotNone(results)
        self.assertIn('modules', results)
        self.assertIn('overview', results)
        self.assertIn('origin', results)
        self.assertIn('endemism', results)
        self.assertIn('cons_status_global', results)
        self.assertIn('cons_status_national', results)

    @patch('bims.utils.celery.memcache_lock')
    def test_summary_task_overview_data(self, mock_lock):
        from bims.tasks.spatial_dashboard import spatial_dashboard_summary

        mock_lock.return_value.__enter__ = lambda s: True
        mock_lock.return_value.__exit__ = lambda s, *a: None

        search_process = self._create_search_process(
            SPATIAL_DASHBOARD_SUMMARY
        )
        spatial_dashboard_summary(
            search_parameters=self.search_params,
            search_process_id=search_process.id,
        )
        search_process.refresh_from_db()
        results = search_process.get_file_if_exits()
        overview = results['overview']
        self.assertIn('Number of Taxa', overview)
        taxa_counts = overview['Number of Taxa']
        self.assertIn('Fish', taxa_counts)
        self.assertEqual(taxa_counts['Fish'], 2)

    @patch('bims.utils.celery.memcache_lock')
    def test_map_task(self, mock_lock):
        from bims.tasks.spatial_dashboard import spatial_dashboard_map

        mock_lock.return_value.__enter__ = lambda s: True
        mock_lock.return_value.__exit__ = lambda s, *a: None

        search_process = self._create_search_process(
            SPATIAL_DASHBOARD_MAP
        )
        spatial_dashboard_map(
            search_parameters=self.search_params,
            search_process_id=search_process.id,
        )
        search_process.refresh_from_db()
        self.assertTrue(search_process.finished)
        results = search_process.get_file_if_exits()
        self.assertIsNotNone(results)
        self.assertIn('extent', results)
        self.assertIn('sites_raw_query', results)

    def test_task_with_nonexistent_search_process(self):
        from bims.tasks.spatial_dashboard import spatial_dashboard_cons_status

        # Should not raise an exception
        result = spatial_dashboard_cons_status(
            search_parameters={},
            search_process_id=99999,
        )
        self.assertIsNone(result)
