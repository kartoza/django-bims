from django.test import TestCase
from django.urls import reverse
from django_tenants.test.cases import FastTenantTestCase
from django_tenants.test.client import TenantClient

from bims.models.taxon_origin import TaxonOrigin
from bims.tests.model_factories import (
    BiologicalCollectionRecordF,
    LocationSiteF,
    TaxonomyF,
    IUCNStatusF,
    EndemismF
)


class TestLocationSiteDashboard(FastTenantTestCase):
    """
    Tests location site dashboard
    """
    def setUp(self):
        endemism = EndemismF.create(
            name='endemism_1'
        )
        endemism_2 = EndemismF.create(
            name='endemism_2'
        )
        iucn_status_lc = IUCNStatusF.create(
            category='LC'
        )
        iucn_status_ne = IUCNStatusF.create(
            category='NE'
        )
        taxa = TaxonomyF.create(
            origin=TaxonOrigin.objects.get_or_create(
                category='Native', origin_key='indigenous',
                defaults={'order': 1})[0],
            scientific_name='taxa_1',
            iucn_status=iucn_status_lc,
            endemism=endemism
        )
        taxa_2 = TaxonomyF.create(
            origin=TaxonOrigin.objects.get_or_create(
                category='Unknown', origin_key='unknown',
                defaults={'order': 2})[0],
            scientific_name='taxa_2',
            iucn_status=iucn_status_ne,
            endemism=endemism_2
        )
        BiologicalCollectionRecordF.create(
            original_species_name='test1',
            collection_date='2000-12-12',
            taxonomy=taxa
        )
        BiologicalCollectionRecordF.create(
            original_species_name='test3',
            collection_date='2000-12-01',
            taxonomy=taxa
        )
        BiologicalCollectionRecordF.create(
            original_species_name='test2',
            collection_date='2001-10-10',
            taxonomy=taxa_2
        )
        self.client = TenantClient(self.tenant)

    def test_occurrences_chart_data_by_year(self):
        url = reverse('location-sites-occurrences-chart-data')

        data = {
            'search': 'test',
            'd': 'y',
        }
        response = self.client.get(url, data)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.data['labels'],
            [2000, 2001]
        )
        self.assertEqual(
            response.data['dataset_labels'],
            ['Native', 'Unknown']
        )
        self.assertEqual(
            response.data['data']['Native'],
            [2, 0]
        )
        self.assertEqual(
            response.data['data']['Unknown'],
            [0, 1]
        )

    def test_occurrences_chart_data_by_month(self):
        url = reverse('location-sites-occurrences-chart-data')

        data = {
            'search': 'test',
            'd': 'm',
        }
        response = self.client.get(url, data)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.data['labels'],
            ['12-2000', '10-2001']
        )
        self.assertEqual(
            response.data['dataset_labels'],
            ['Native', 'Unknown']
        )

    def test_conservation_chart_data_by_year(self):
        url = reverse('location-sites-cons-chart-data')

        data = {
            'search': 'test',
            'd': 'y',
        }
        response = self.client.get(url, data)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.data['labels'],
            [2000, 2001]
        )
        self.assertEqual(
            response.data['dataset_labels'],
            ['LC', 'NE']
        )
        self.assertEqual(
            response.data['data']['LC'],
            [2, 0]
        )
        self.assertEqual(
            response.data['data']['NE'],
            [0, 1]
        )

    def test_conservation_chart_data_by_month(self):
        url = reverse('location-sites-cons-chart-data')

        data = {
            'search': 'test',
            'd': 'm',
        }
        response = self.client.get(url, data)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.data['labels'],
            ['12-2000', '10-2001']
        )
        self.assertEqual(
            response.data['dataset_labels'],
            ['LC', 'NE']
        )

    def test_endemism_chart_data_by_year(self):
        url = reverse('location-sites-endemism-chart-data')

        data = {
            'search': 'test',
            'd': 'y',
        }
        response = self.client.get(url, data)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.data['labels'],
            [2000, 2001]
        )
        self.assertEqual(
            response.data['dataset_labels'],
            ['endemism_1', 'endemism_2']
        )
        self.assertEqual(
            response.data['data']['endemism_1'],
            [2, 0]
        )
        self.assertEqual(
            response.data['data']['endemism_2'],
            [0, 1]
        )

    def test_endemism_chart_data_by_month(self):
        url = reverse('location-sites-endemism-chart-data')

        data = {
            'search': 'test',
            'd': 'm',
        }
        response = self.client.get(url, data)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.data['labels'],
            ['12-2000', '10-2001']
        )
        self.assertEqual(
            response.data['dataset_labels'],
            ['endemism_1', 'endemism_2']
        )

    def test_site_taxa_chart_data_by_year(self):
        url = reverse('location-sites-taxa-chart-data')

        data = {
            'search': 'test',
            'd': 'y',
        }
        response = self.client.get(url, data)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.data['labels'],
            [2000, 2001]
        )
        self.assertEqual(
            response.data['dataset_labels'],
            ['taxa_1', 'taxa_2']
        )
        self.assertEqual(
            response.data['data']['taxa_1'],
            [2, 0]
        )
        self.assertEqual(
            response.data['data']['taxa_2'],
            [0, 1]
        )

    def test_site_taxa_chart_data_by_month(self):
        url = reverse('location-sites-taxa-chart-data')

        data = {
            'search': 'test',
            'd': 'm',
        }
        response = self.client.get(url, data)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.data['labels'],
            ['12-2000', '10-2001']
        )
        self.assertEqual(
            response.data['dataset_labels'],
            ['taxa_1', 'taxa_2']
        )
