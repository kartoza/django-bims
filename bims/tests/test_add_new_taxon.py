from django.test import TestCase
from django.urls import reverse
from django_tenants.test.cases import FastTenantTestCase
from django_tenants.test.client import TenantClient
from rest_framework.test import APIClient
from unittest.mock import patch

from django.contrib.auth.models import User
from bims.tests.model_factories import TaxonomyF, TaxonGroupF, UserF, IUCNStatusF


def mock_update_taxonomy_from_gbif(key, fetch_parent=True, get_vernacular=True):
    iucn_status = IUCNStatusF.create()
    taxonomy = TaxonomyF.create(
        gbif_key=key,
        scientific_name="Mocked Scientific Name",
        canonical_name="Mocked Canonical Name",
        iucn_status=iucn_status
    )
    return taxonomy

class AddNewTaxonTestCase(FastTenantTestCase):
    def setUp(self):
        self.client = TenantClient(self.tenant)
        self.user = UserF.create(username='testuser', password='testpassword')
        self.client.login(username='testuser', password='testpassword')
        self.taxon_group = TaxonGroupF.create(
            name='test'
        )
        self.taxonomy = TaxonomyF()

    @patch('bims.api_views.taxon.update_taxonomy_from_gbif', side_effect=mock_update_taxonomy_from_gbif)
    def test_add_new_taxon_with_gbif_key(self, mock_update):
        data = {
            'gbifKey': '1',
            'taxonName': 'Test Taxon',
            'taxonGroup': self.taxon_group.name,
            'rank': 'species',
            'authorName': 'Test Author',
        }
        response = self.client.post(reverse('add-new-taxon'), data)
        self.assertEqual(response.status_code, 200)
        self.assertTrue('id' in response.data)
        self.assertTrue('taxon_name' in response.data)
        self.assertEqual(response.data['taxon_name'], 'Mocked Canonical Name')

    @patch('bims.api_views.taxon.update_taxonomy_from_gbif', side_effect=mock_update_taxonomy_from_gbif)
    def test_add_new_taxon_without_gbif_key(self, mock_update):
        data = {
            'taxonName': 'Test Taxon Without GBIF',
            'taxonGroup': self.taxon_group.name,
            'rank': 'species',
            'parentId': self.taxonomy.id,
            'authorName': 'Test Author Without GBIF',
        }
        response = self.client.post(reverse('add-new-taxon'), data)
        self.assertEqual(response.status_code, 200)
        self.assertTrue('id' in response.data)
        self.assertTrue('taxon_name' in response.data)
        self.assertEqual(response.data['taxon_name'], 'Test Taxon Without GBIF')

        data = {
            'taxonName': 'Test Taxon Without GBIF 2',
            'taxonGroupId': self.taxon_group.id,
            'rank': 'species',
            'familyId': self.taxonomy.id,
            'authorName': 'Test Author Without GBIF 2',
        }
        response = self.client.post(reverse('add-new-taxon'), data)
        self.assertEqual(response.status_code, 200)
        self.assertTrue('id' in response.data)
        self.assertTrue('taxon_name' in response.data)
        self.assertEqual(response.data['taxon_name'], 'Test Taxon Without GBIF 2')
