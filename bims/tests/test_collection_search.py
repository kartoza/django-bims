from datetime import datetime

from dateutil.relativedelta import relativedelta
from django.contrib.auth.models import Group
from django.test import TestCase
from django.db import connection
from django.contrib.sites.models import Site
from taggit.models import Tag

from bims.models import format_search_result_raw_query
from bims.tests.model_factories import (
    BiologicalCollectionRecordF,
    TaxonomyF,
    LocationSiteF,
    RiverF,
    VernacularNameF, UserF, GroupF
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
        self.tag_name = 'invasive_tag'
        self.taxa.tags.add(self.tag_name)

        self.river = RiverF.create(
            name='original_river_name'
        )
        self.site = LocationSiteF.create(
            site_code='TEST123',
            legacy_river_name='legacy_river_name',
            river=self.river
        )
        self.site2 = LocationSiteF.create(
            site_code='TEST124',
            legacy_river_name='legacy_river_name',
            river=self.river
        )
        BiologicalCollectionRecordF.create(
            original_species_name='test',
            taxonomy=self.taxa,
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

    def test_search_by_taxon_tag_name(self):
        """
        Free-text search should fall back to searching taxonomy tags
        if names/common names/etc. don't match.
        We added self.tag_name as a tag on self.taxa in setUp.
        """
        filters = {
            'search': self.tag_name
        }
        search = CollectionSearch(filters)
        collection_results = search.process_search()

        self.assertGreater(
            collection_results.count(),
            0,
            msg="Expected records when searching by tag name"
        )

    def test_filter_by_taxon_tags_param(self):
        """
        Passing ?tags=["invasive_tag"] should filter to taxa that have that tag.
        CollectionSearch.taxon_tags parses JSON string -> ['invasive_tag']
        and we add a JOIN filter taxonomy__tags__name__in.
        """
        taxon_tag_id = Tag.objects.get(name='invasive_tag').id
        filters = {
            'tags': '["%s"]' % taxon_tag_id
        }
        search = CollectionSearch(filters)
        collection_results = search.process_search()

        self.assertGreater(
            collection_results.count(),
            0,
            msg="Expected records when filtering by explicit tags param"
        )

    def test_search_with_data_type(self):
        _user = UserF.create(is_superuser=False)
        _staff = UserF.create(is_superuser=True)
        try:
            group = Group.objects.get(
                name='SensitiveDataGroup'
            )
        except Group.DoesNotExist:
            group = GroupF.create(
                name='SensitiveDataGroup'
            )
        _user.groups.add(group)
        BiologicalCollectionRecordF.create(
            original_species_name='test981',
            taxonomy=self.taxa,
            site=self.site,
            data_type='private'
        )
        BiologicalCollectionRecordF.create(
            original_species_name='test982',
            taxonomy=self.taxa,
            site=self.site,
            data_type='public'
        )
        filters = {
            'search': 'test98',
            'requester': _user.id
        }
        search = CollectionSearch(filters)
        collection_results = search.process_search()
        with connection.cursor() as cursor:
            raw_query = format_search_result_raw_query(search.location_sites_raw_query)
            cursor.execute(raw_query)
            result = cursor.fetchall()
            self.assertEqual(
                len(result),
                1
            )
        self.assertEqual(
            collection_results.count(),
            1
        )

        try:
            private_group = Group.objects.get(
                name='PrivateDataGroup'
            )
        except Group.DoesNotExist:
            private_group = GroupF.create(
                name='PrivateDataGroup'
            )
        _user.groups.add(private_group)

        # Staff
        filters = {
            'search': 'test98',
            'requester': _staff.id
        }
        search = CollectionSearch(filters)
        collection_results = search.process_search()
        with connection.cursor() as cursor:
            raw_query = format_search_result_raw_query(search.location_sites_raw_query)
            cursor.execute(raw_query)
        self.assertEqual(
            collection_results.count(),
            1
        )

        BiologicalCollectionRecordF.create(
            original_species_name='test983',
            taxonomy=self.taxa,
            site=self.site,
            data_type='sensitive'
        )
        filters = {
            'search': 'test98',
            'requester': _user.id
        }
        search = CollectionSearch(filters)
        collection_results = search.process_search()
        with connection.cursor() as cursor:
            raw_query = format_search_result_raw_query(search.location_sites_raw_query)
            cursor.execute(raw_query)
        self.assertEqual(
            collection_results.count(),
            3
        )

    def test_search_embargo_data(self):
        _user = UserF.create(is_superuser=True)
        BiologicalCollectionRecordF.create(
            original_species_name='test99',
            taxonomy=self.taxa,
            site=self.site,
            end_embargo_date=datetime.now() + relativedelta(months=1),
            owner=_user
        )
        BiologicalCollectionRecordF.create(
            original_species_name='test99',
            taxonomy=self.taxa,
            site=self.site2,
            end_embargo_date=datetime.now()
        )
        filters = {
            'search': 'test99',
            'requester': _user.id
        }
        search = CollectionSearch(filters)
        collection_results = search.process_search()
        with connection.cursor() as cursor:
            raw_query = format_search_result_raw_query(search.location_sites_raw_query)
            cursor.execute(raw_query)
            result = cursor.fetchall()
            self.assertEqual(
                len(result),
                2
            )
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
        with connection.cursor() as cursor:
            raw_query = format_search_result_raw_query(search.location_sites_raw_query)
            cursor.execute(raw_query)
            result = cursor.fetchall()
            self.assertEqual(
                len(result),
                1
            )
