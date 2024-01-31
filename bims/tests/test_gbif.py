# coding=utf-8
"""Tests for models."""
from django.contrib.gis.geos import GEOSGeometry
from django.test import TestCase, Client
from unittest.mock import patch, MagicMock
from allauth.utils import get_user_model
from bims.tests.model_factories import (
    LocationSiteF,
)
from bims.tests.model_factories import BoundaryF
from bims.utils.gbif import find_species_by_area


class TestGBIFUtil(TestCase):
    """ Tests Fish Form View.
    """

    def test_geometry_not_found(self):
        boundary = BoundaryF.create()
        species = find_species_by_area(
            boundary.id
        )
        self.assertEqual(species, [])

    def test_boundary_not_found(self):
        species = find_species_by_area(
            9999
        )
        self.assertEqual(species, [])

    @patch('bims.utils.gbif.search')
    @patch('bims.utils.gbif.get_species')
    def test_successful_data_retrieval(self, mock_get_species, mock_search):
        boundary = BoundaryF.create(
            geometry=GEOSGeometry('MULTIPOLYGON(((0 0, 4 0, 4 4, 0 4, 0 0), (10 10, 14 10, 14 14, 10 14, 10 10)))')
        )
        mock_search.return_value = {
            'results': [{'acceptedTaxonKey': 1}, {'acceptedTaxonKey': 2}],
            'endOfRecords': False,
            'limit': 2
        }
        mock_get_species.side_effect = lambda x: f'species_data_{x}'
        species = find_species_by_area(boundary.id, max_limit=1)

        # Assertions
        self.assertEqual(len(species), 2)
        self.assertIn('species_data_1', species)
        self.assertIn('species_data_2', species)

    @patch('bims.utils.gbif.search')
    def test_error_handling(self, mock_search):
        boundary = BoundaryF.create(
            geometry=GEOSGeometry('MULTIPOLYGON(((0 0, 4 0, 4 4, 0 4, 0 0), (10 10, 14 10, 14 14, 10 14, 10 10)))')
        )
        mock_search.side_effect = Exception("General Error")

        species = find_species_by_area(boundary.id)
        self.assertEqual(species, [])

    @patch('bims.utils.gbif.search')
    @patch('bims.utils.gbif.get_species')
    def test_error_handling_get_species(self, mock_get_species, mock_search):
        boundary = BoundaryF.create(
            geometry=GEOSGeometry('MULTIPOLYGON(((0 0, 4 0, 4 4, 0 4, 0 0), (10 10, 14 10, 14 14, 10 14, 10 10)))')
        )
        mock_search.return_value = {
            'results': [{'acceptedTaxonKey': 1}, {'acceptedTaxonKey': 2}],
            'endOfRecords': False,
            'limit': 2
        }
        mock_get_species.side_effect = Exception("General Error")
        species = find_species_by_area(boundary.id)

        self.assertEqual(species, [])

