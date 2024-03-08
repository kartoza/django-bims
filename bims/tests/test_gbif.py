# coding=utf-8
"""Tests for models."""
from django.contrib.gis.geos import GEOSGeometry
from django.test import TestCase, Client
from unittest.mock import patch, MagicMock
from allauth.utils import get_user_model
from bims.tests.model_factories import (
    LocationSiteF, TaxonomyF,
    HarvestSessionF
)
from bims.tests.model_factories import BoundaryF
from bims.utils.gbif import find_species_by_area
from bims.models import TaxonGroup


class TestGBIFUtil(TestCase):
    """ Tests Fish Form View.
    """
    def setUp(self):
        self.taxon = TaxonomyF.create()

    def test_geometry_not_found(self):
        boundary = BoundaryF.create()
        species = find_species_by_area(
            boundary.id,
            parent_species=self.taxon
        )
        self.assertEqual(species, [])

    def test_boundary_not_found(self):
        species = find_species_by_area(
            9999,
            parent_species=self.taxon
        )
        self.assertEqual(species, [])

    @patch('bims.utils.gbif.search')
    @patch('bims.utils.fetch_gbif.fetch_all_species_from_gbif')
    def test_successful_data_retrieval(self, mock_get_species, mock_search):
        boundary = BoundaryF.create(
            geometry=GEOSGeometry('MULTIPOLYGON(((0 0, 4 0, 4 4, 0 4, 0 0), (10 10, 14 10, 14 14, 10 14, 10 10)))')
        )
        mock_search.return_value = {
            'results': [{'acceptedTaxonKey': 1}, {'acceptedTaxonKey': 2}],
            'endOfRecords': False,
            'limit': 2
        }
        harvest_session = HarvestSessionF.create()
        taxon_1 = TaxonomyF.create()
        taxon_2 = TaxonomyF.create()
        mock_get_species.side_effect = [
            taxon_1,
            taxon_2
        ]
        species = find_species_by_area(boundary.id, max_limit=1, harvest_session=harvest_session,
                                       parent_species=self.taxon)

        # Assertions
        self.assertEqual(len(species), 2)
        self.assertIn(taxon_1, species)
        self.assertIn(taxon_2, species)

        taxon_group = TaxonGroup.objects.get(id=harvest_session.module_group.id)
        self.assertTrue(
            taxon_1 in
            taxon_group.taxonomies.all()
        )

    @patch('bims.utils.gbif.search')
    def test_error_handling(self, mock_search):
        boundary = BoundaryF.create(
            geometry=GEOSGeometry('MULTIPOLYGON(((0 0, 4 0, 4 4, 0 4, 0 0), (10 10, 14 10, 14 14, 10 14, 10 10)))')
        )
        mock_search.side_effect = Exception("General Error")

        species = find_species_by_area(boundary.id,
                                       parent_species=self.taxon)
        self.assertEqual(species, [])

    @patch('bims.utils.gbif.search')
    @patch('bims.utils.fetch_gbif.fetch_all_species_from_gbif')
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
        species = find_species_by_area(boundary.id,
                                       parent_species=self.taxon)

        self.assertEqual(species, [])

    @patch('bims.utils.gbif.search')
    @patch('bims.utils.fetch_gbif.fetch_all_species_from_gbif')
    def test_canceled_harvest(self, mock_get_species, mock_search):
        boundary = BoundaryF.create(
            geometry=GEOSGeometry('MULTIPOLYGON(((0 0, 4 0, 4 4, 0 4, 0 0), (10 10, 14 10, 14 14, 10 14, 10 10)))')
        )
        mock_search.return_value = {
            'results': [{'acceptedTaxonKey': 1}, {'acceptedTaxonKey': 2}],
            'endOfRecords': False,
            'limit': 2
        }
        taxon_1 = TaxonomyF.create()
        taxon_2 = TaxonomyF.create()
        mock_get_species.side_effect = [
            taxon_1,
            taxon_2
        ]
        harvest_session = HarvestSessionF.create(
            canceled=True
        )
        species = find_species_by_area(
            boundary.id, max_limit=1,
            harvest_session=harvest_session,
            parent_species=self.taxon)

        self.assertEqual(
            species,
            None
        )

