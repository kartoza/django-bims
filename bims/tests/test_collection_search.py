from datetime import datetime

from dateutil.relativedelta import relativedelta
from django.test import TestCase
from django.contrib.sites.models import Site
from bims.tests.model_factories import (
    BiologicalCollectionRecordF,
    TaxonomyF,
    LocationSiteF,
    RiverF,
    VernacularNameF, UserF
)
from bims.api_views.search import CollectionSearch


class TestCollectionSearch(TestCase):

    def setUp(self):
        """
        Sets up before each test
        """
        vernacular_name_1 = VernacularNameF.create(
            name='common_name_1'
        )
        self.taxa = TaxonomyF.create(
            canonical_name='test',
            scientific_name='scientific_test',
            vernacular_names=(vernacular_name_1, )
        )
        self.river = RiverF.create(
            name='original_river_name'
        )
        self.site = LocationSiteF.create(
            site_code='TEST123',
            legacy_river_name='legacy_river_name',
            river=self.river
        )
        BiologicalCollectionRecordF.create(
            original_species_name='test',
            taxonomy=self.taxa,
            source_site=Site.objects.get_current(),
            site=self.site
        )

    def test_search_by_taxonomy_name(self):
        filters = {
            'search': 'test'
        }
        search = CollectionSearch(filters)
        collection_results = search.process_search()
        self.assertGreater(
            collection_results.count(),
            0
        )

    def test_search_by_taxonomy_scientific_name(self):
        filters = {
            'search': 'scientific_test'
        }
        search = CollectionSearch(filters)
        collection_results = search.process_search()
        self.assertGreater(
            collection_results.count(),
            0
        )

    def test_search_by_site_code(self):
        filters = {
            'search': 'TEST123'
        }
        search = CollectionSearch(filters)
        collection_results = search.process_search()
        self.assertGreater(
            collection_results.count(),
            0
        )

    def test_search_by_legacy_river_name(self):
        filters = {
            'search': 'legacy_river_name'
        }
        search = CollectionSearch(filters)
        collection_results = search.process_search()
        self.assertGreater(
            collection_results.count(),
            0
        )

    def test_search_by_river_name(self):
        filters = {
            'search': 'original_river_name'
        }
        search = CollectionSearch(filters)
        collection_results = search.process_search()
        self.assertGreater(
            collection_results.count(),
            0
        )

    def test_search_by_vernacular_name(self):
        filters = {
            'search': 'common_name_1'
        }
        search = CollectionSearch(filters)
        collection_results = search.process_search()
        self.assertGreater(
            collection_results.count(),
            0
        )

    def test_search_embargo_data(self):
        _user = UserF.create(is_superuser=True)
        BiologicalCollectionRecordF.create(
            original_species_name='test99',
            taxonomy=self.taxa,
            source_site=Site.objects.get_current(),
            site=self.site,
            end_embargo_date=datetime.now() + relativedelta(months=1),
            owner=_user
        )
        BiologicalCollectionRecordF.create(
            original_species_name='test99',
            taxonomy=self.taxa,
            source_site=Site.objects.get_current(),
            site=self.site,
            end_embargo_date=datetime.now()
        )
        filters = {
            'search': 'test99',
            'requester': _user.id
        }
        search = CollectionSearch(filters)
        collection_results = search.process_search()
        self.assertEqual(
            collection_results.count(),
            2
        )
        filters = {
            'search': 'test99',
        }
        search = CollectionSearch(filters)
        collection_results = search.process_search()
        self.assertEqual(
            collection_results.count(),
            1
        )
