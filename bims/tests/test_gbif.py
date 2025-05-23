# coding=utf-8
"""Tests for the GBIF utility."""
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

from django.contrib.gis.geos import GEOSGeometry
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase

from bims.tests.model_factories import (
    BoundaryF, HarvestSessionF, TaxonomyF
)
from bims.utils.gbif_download import find_species_by_area

os.environ.setdefault("GBIF_USERNAME", "dummy_user")
os.environ.setdefault("GBIF_PASSWORD", "dummy_pass")


class TestGBIFUtil(TestCase):
    def setUp(self):
        self.taxon = TaxonomyF.create()

    def test_geometry_not_found(self):
        boundary = BoundaryF.create()
        species = find_species_by_area(boundary.id, parent_species=self.taxon)
        self.assertEqual(species, [])

    def test_boundary_not_found(self):
        species = find_species_by_area(9999, parent_species=self.taxon)
        self.assertEqual(species, [])

    @patch(
        "bims.utils.fetch_gbif.fetch_all_species_from_gbif", create=True
    )
    @patch('bims.utils.gbif_download.submit_download', return_value='dummy')
    @patch('bims.utils.gbif_download.get_ready_download_url', return_value='https://x/d.zip')
    @patch('bims.utils.gbif_download.download_archive', return_value=Path('/tmp/dummy.zip'))
    @patch('bims.utils.gbif_download.extract_species_keys',
           side_effect=lambda _p, s, _m, _log: s.update({1, 2}))
    def test_successful_data_retrieval(
        self,
        mock_extract,
        mock_download,
        mock_ready,
        mock_submit,
        mock_fetch_taxon,
    ):
        boundary = BoundaryF.create(
            geometry=GEOSGeometry(
                "MULTIPOLYGON(((0 0,4 0,4 4,0 4,0 0)),"
                "((10 10,14 10,14 14,10 14,10 10)))"
            )
        )

        mock_submit.side_effect = "dummy"

        harvest_session = HarvestSessionF.create(
            log_file=SimpleUploadedFile("test.log", b"")
        )

        taxon_1 = TaxonomyF.create()
        taxon_2 = TaxonomyF.create()
        mock_fetch_taxon.side_effect = [taxon_1, taxon_2]

        species = find_species_by_area(
            boundary.id,
            self.taxon,
            harvest_session=harvest_session,
            max_limit=1,
        )

        self.assertEqual(len(species), 2)
        self.assertIn(taxon_1, species)
        self.assertIn(taxon_2, species)

    @patch("bims.utils.gbif._submit_download", side_effect=Exception("Boom"), create=True)
    def test_error_handling(self, _mock_submit):
        boundary = BoundaryF.create(
            geometry=GEOSGeometry(
                "MULTIPOLYGON(((0 0,4 0,4 4,0 4,0 0)),"
                "((10 10,14 10,14 14,10 14,10 10)))"
            )
        )
        species = find_species_by_area(boundary.id, parent_species=self.taxon)
        self.assertEqual(species, [])

    @patch("bims.utils.gbif.fetch_all_species_from_gbif",
           side_effect=Exception("Boom"), create=True)
    @patch("bims.utils.gbif._extract_species_keys",
           side_effect=lambda _p, s, _m=None: s.update({1, 2}), create=True)
    @patch("bims.utils.gbif_download.download_archive", return_value=Path("/tmp/dummy.zip"), create=True)
    @patch("bims.utils.gbif_download.get_ready_download_url", return_value="https://x/d.zip", create=True)
    @patch("bims.utils.gbif_download.submit_download", return_value="dummy", create=True)
    def test_error_handling_get_species(
        self,
        _mock_submit,
        _mock_ready,
        _mock_download,
        _mock_extract,
        _mock_fetch_tax,
    ):
        boundary = BoundaryF.create(
            geometry=GEOSGeometry(
                "MULTIPOLYGON(((0 0,4 0,4 4,0 4,0 0)),"
                "((10 10,14 10,14 14,10 14,10 10)))"
            )
        )
        species = find_species_by_area(boundary.id, parent_species=self.taxon)
        self.assertEqual(species, [])

    @patch("bims.utils.gbif._extract_species_keys",
           side_effect=lambda _p, s, _m=None: s.update({1, 2}), create=True)
    @patch("bims.utils.gbif_download.download_archive", return_value=Path("/tmp/dummy.zip"), create=True)
    @patch("bims.utils.gbif_download.get_ready_download_url", return_value="https://x/d.zip", create=True)
    @patch("bims.utils.gbif_download.submit_download", return_value="dummy", create=True)
    def test_canceled_harvest(
        self,
        _mock_submit,
        _mock_ready,
        _mock_download,
        _mock_extract,
    ):
        # geometry with two polygons
        boundary = BoundaryF.create(
            geometry=GEOSGeometry(
                "MULTIPOLYGON(((0 0,4 0,4 4,0 4,0 0)),"
                "((10 10,14 10,14 14,10 14,10 10)))"
            )
        )

        harvest_session = HarvestSessionF.create(
            canceled=True,
            log_file=SimpleUploadedFile("test.log", b""),
        )

        species = find_species_by_area(
            boundary.id,
            max_limit=1,
            harvest_session=harvest_session,
            parent_species=self.taxon,
        )

        # when cancelled, the helper should return an **empty list**
        self.assertEqual(species, [])