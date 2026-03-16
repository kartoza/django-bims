# coding=utf-8
"""Tests that SASS dashboard views pass requester_id to CollectionSearch
so data owners can access their own embargoed records."""
import datetime
import factory
from unittest.mock import patch, MagicMock
from django.db.models import signals
from django_tenants.test.cases import FastTenantTestCase
from django_tenants.test.client import TenantClient

from bims.api_views.search import CollectionSearch
from bims.tests.model_factories import UserF, LocationSiteF
from sass.models import SiteVisitTaxon
from sass.tests.model_factories import SiteVisitF, SiteVisitTaxonF


def _future_embargo():
    return datetime.date.today() + datetime.timedelta(days=30)


class TestSassDashboardEmbargoRequester(FastTenantTestCase):
    """Verify that every SASS view passes the authenticated user's id as
    requester_id to CollectionSearch so embargo owner checks work."""

    def setUp(self):
        self.client = TenantClient(self.tenant)
        self.owner = UserF.create()
        self.site = LocationSiteF.create()

    def _mock_search(self, empty=True):
        mock_instance = MagicMock()
        mock_instance.process_search.return_value = SiteVisitTaxon.objects.none()
        mock_instance.sass_only = False
        return mock_instance

    @factory.django.mute_signals(signals.pre_save, signals.post_save)
    def test_single_site_dashboard_passes_requester_id(self):
        """Authenticated user's id is forwarded to CollectionSearch."""
        self.client.login(username=self.owner.username, password='password')
        with patch('sass.views.sass_dashboard.CollectionSearch') as MockSearch:
            MockSearch.return_value = self._mock_search()
            self.client.get(
                f'/sass/dashboard/{self.site.id}/?siteId={self.site.id}'
            )
        MockSearch.assert_called_once()
        _, call_kwargs = MockSearch.call_args
        self.assertEqual(call_kwargs.get('requester_id'), self.owner.id)

    @factory.django.mute_signals(signals.pre_save, signals.post_save)
    def test_single_site_dashboard_anonymous_passes_none(self):
        """Anonymous requests forward requester_id=None."""
        with patch('sass.views.sass_dashboard.CollectionSearch') as MockSearch:
            MockSearch.return_value = self._mock_search()
            self.client.get(
                f'/sass/dashboard/{self.site.id}/?siteId={self.site.id}'
            )
        _, call_kwargs = MockSearch.call_args
        self.assertIsNone(call_kwargs.get('requester_id'))

    @factory.django.mute_signals(signals.pre_save, signals.post_save)
    def test_multiple_sites_api_passes_requester_id(self):
        """Multiple-sites API forwards the authenticated user's id."""
        self.client.login(username=self.owner.username, password='password')
        with patch(
            'sass.views.sass_dashboard_multiple.CollectionSearch'
        ) as MockSearch:
            mock_inst = self._mock_search()
            mock_inst.process_search.return_value = (
                SiteVisitTaxon.objects.none()
            )
            MockSearch.return_value = mock_inst
            self.client.get('/sass/dashboard-multi-sites-api/')
        MockSearch.assert_called_once()
        _, call_kwargs = MockSearch.call_args
        self.assertEqual(call_kwargs.get('requester_id'), self.owner.id)

    @factory.django.mute_signals(signals.pre_save, signals.post_save)
    def test_download_sass_data_passes_requester_id(self):
        """download_sass_data_site forwards the authenticated user's id."""
        self.client.login(username=self.owner.username, password='password')
        with patch(
            'sass.views.download_sass_data_site.CollectionSearch'
        ) as MockSearch:
            MockSearch.return_value = self._mock_search()
            self.client.get('/sass/download-sass-data-site/')
        MockSearch.assert_called_once()
        _, call_kwargs = MockSearch.call_args
        self.assertEqual(call_kwargs.get('requester_id'), self.owner.id)

    @factory.django.mute_signals(signals.pre_save, signals.post_save)
    def test_download_sass_summary_passes_requester_id(self):
        """download_sass_summary_data forwards the authenticated user's id."""
        self.client.login(username=self.owner.username, password='password')
        with patch(
            'sass.views.download_sass_data_site.CollectionSearch'
        ) as MockSearch:
            MockSearch.return_value = self._mock_search()
            self.client.get('/sass/download-sass-summary-data/')
        MockSearch.assert_called_once()
        _, call_kwargs = MockSearch.call_args
        self.assertEqual(call_kwargs.get('requester_id'), self.owner.id)


class TestSassDashboardEmbargoAccess(FastTenantTestCase):
    """Integration tests: owners see their embargoed data; others do not."""

    def setUp(self):
        self.client = TenantClient(self.tenant)
        self.owner = UserF.create()
        self.other_user = UserF.create()
        self.site = LocationSiteF.create()

    @factory.django.mute_signals(signals.pre_save, signals.post_save)
    def _create_embargoed_taxon(self):
        site_visit = SiteVisitF.create(
            location_site=self.site,
            owner=self.owner,
        )
        return SiteVisitTaxonF.create(
            site_visit=site_visit,
            site=self.site,
            owner=self.owner,
            end_embargo_date=_future_embargo(),
        )

    @factory.django.mute_signals(signals.pre_save, signals.post_save)
    def test_collection_search_owner_sees_embargoed_record(self):
        """CollectionSearch returns an embargoed record when requester is the owner."""
        svt = self._create_embargoed_taxon()
        search = CollectionSearch(
            {'siteId': str(self.site.id)},
            requester_id=self.owner.id,
        )
        result_ids = list(search.process_search().values_list('id', flat=True))
        self.assertIn(svt.id, result_ids)

    @factory.django.mute_signals(signals.pre_save, signals.post_save)
    def test_collection_search_other_user_cannot_see_embargoed_record(self):
        """CollectionSearch excludes an embargoed record for non-owners."""
        svt = self._create_embargoed_taxon()
        search = CollectionSearch(
            {'siteId': str(self.site.id)},
            requester_id=self.other_user.id,
        )
        result_ids = list(search.process_search().values_list('id', flat=True))
        self.assertNotIn(svt.id, result_ids)

    @factory.django.mute_signals(signals.pre_save, signals.post_save)
    def test_collection_search_anonymous_cannot_see_embargoed_record(self):
        """CollectionSearch excludes embargoed records for unauthenticated requests."""
        svt = self._create_embargoed_taxon()
        search = CollectionSearch(
            {'siteId': str(self.site.id)},
            requester_id=None,
        )
        result_ids = list(search.process_search().values_list('id', flat=True))
        self.assertNotIn(svt.id, result_ids)

    @factory.django.mute_signals(signals.pre_save, signals.post_save)
    def test_single_site_dashboard_owner_sees_sass_exists(self):
        """Single-site dashboard sets sass_exists=True for data owners with active embargo."""
        self._create_embargoed_taxon()
        self.client.login(username=self.owner.username, password='password')
        response = self.client.get(
            f'/sass/dashboard/{self.site.id}/?siteId={self.site.id}'
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['sass_exists'])

    @factory.django.mute_signals(signals.pre_save, signals.post_save)
    def test_single_site_dashboard_other_user_sass_not_exists(self):
        """Single-site dashboard sets sass_exists=False for non-owners with active embargo."""
        self._create_embargoed_taxon()
        self.client.login(username=self.other_user.username, password='password')
        response = self.client.get(
            f'/sass/dashboard/{self.site.id}/?siteId={self.site.id}'
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context['sass_exists'])
