from django.test import TestCase
from unittest.mock import patch
from bims.utils.cites import CitesSpeciesPlusAPI
from django.conf import settings


class TestCitesSpeciesPlusAPI(TestCase):

    def setUp(self):
        self.api = CitesSpeciesPlusAPI()
        self.taxon_concept_id = 1234  # Example ID, replace with a relevant one

    def test_initialization(self):
        """Test the initialization of the CitesSpeciesPlusAPI class."""
        self.assertEqual(self.api.base_url, "https://api.speciesplus.net/api/v1")

    @patch('bims.utils.cites.requests.get')
    def test_get_cites_legislation(self, mock_get):
        """Test the get_cites_legislation method."""
        self.api.get_cites_legislation(self.taxon_concept_id)
        mock_get.assert_called_once_with(
            f"https://api.speciesplus.net/api/v1/taxon_concepts/{self.taxon_concept_id}/cites_legislation",
            headers=self.api.headers,
            params=None
        )

    @patch('bims.utils.cites.requests.get')
    def test_get_distributions(self, mock_get):
        """Test the get_distributions method."""
        self.api.get_distributions(self.taxon_concept_id)
        mock_get.assert_called_once_with(
            f"https://api.speciesplus.net/api/v1/taxon_concepts/{self.taxon_concept_id}/distributions",
            headers=self.api.headers,
            params=None
        )

    @patch('bims.utils.cites.requests.get')
    def test_get_eu_legislation(self, mock_get):
        """Test the get_eu_legislation method."""
        self.api.get_eu_legislation(self.taxon_concept_id)
        mock_get.assert_called_once_with(
            f"https://api.speciesplus.net/api/v1/taxon_concepts/{self.taxon_concept_id}/eu_legislation",
            headers=self.api.headers,
            params=None
        )

    @patch('bims.utils.cites.requests.get')
    def test_get_references(self, mock_get):
        """Test the get_references method."""
        self.api.get_references(self.taxon_concept_id)
        mock_get.assert_called_once_with(
            f"https://api.speciesplus.net/api/v1/taxon_concepts/{self.taxon_concept_id}/references",
            headers=self.api.headers,
            params=None
        )

    @patch('bims.utils.cites.requests.get')
    def test_list_taxon_concepts(self, mock_get):
        """Test the list_taxon_concepts method."""
        self.api.list_taxon_concepts(self.taxon_concept_id)
        mock_get.assert_called_once_with(
            f"https://api.speciesplus.net/api/v1/taxon_concepts.json",
            headers=self.api.headers,
            params=self.taxon_concept_id
        )
