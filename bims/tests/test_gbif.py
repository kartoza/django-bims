# coding=utf-8
"""Tests for the GBIF utility."""
import json
import os
from pathlib import Path
from unittest.mock import patch

from django.contrib.gis.geos import GEOSGeometry
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from preferences import preferences

from bims.models import SiteSetting
from bims.scripts.import_gbif_occurrences import BOUNDARY_BATCH_SIZE
from bims.tests.model_factories import (
    BoundaryF, HarvestSessionF, TaxonomyF
)
from bims.utils import gbif_download as gd
from bims.utils.gbif_download import find_species_by_area

os.environ.setdefault("GBIF_USERNAME", "dummy_user")
os.environ.setdefault("GBIF_PASSWORD", "dummy_pass")


class TestGBIFUtil(TestCase):
    def setUp(self):
        self.taxon = TaxonomyF.create()

        site_setting = getattr(preferences, "SiteSetting", None)
        if not site_setting or not getattr(site_setting, "id", None):
            site_setting = SiteSetting.objects.create()
        site_setting.gbif_username = "test"
        site_setting.gbif_password = "test"
        site_setting.save()

    def _make_boundary_with_two_polys(self):
        return BoundaryF.create(
            geometry=GEOSGeometry(
                "MULTIPOLYGON(((0 0,4 0,4 4,0 4,0 0)),"
                "((10 10,14 10,14 14,10 14,10 10)))"
            )
        )

    def _seed_sidecar(self, harvest_session, keys):
        os.makedirs(gd.SIDECAR_DIR, exist_ok=True)
        sidecar = os.path.join(gd.SIDECAR_DIR, f"{harvest_session.id}_species.json")
        with open(sidecar, "w", encoding="utf-8") as fh:
            json.dump(sorted(keys), fh)

    def _prime_resume_meta(self, harvest_session, boundary, parent, polygon_count):
        """Initialize resume state so the code does NOT wipe the sidecar on first run."""
        state = {
            "next_batch": 1,
            "download_keys": {},
            "meta": {
                "boundary_id": boundary.id,
                "parent_key": getattr(parent, "gbif_key", None),
                "polygon_count": polygon_count,
                "batch_size": BOUNDARY_BATCH_SIZE,
            },
        }
        harvest_session.status = json.dumps(state)
        harvest_session.save(update_fields=["status"])

    def test_geometry_not_found(self):
        boundary = BoundaryF.create()  # no geometry
        species = find_species_by_area(boundary.id, parent_species=self.taxon)
        self.assertEqual(species, [])

    def test_boundary_not_found(self):
        species = find_species_by_area(9999, parent_species=self.taxon)
        self.assertEqual(species, [])

    @patch('bims.utils.fetch_gbif.fetch_all_species_from_gbif', create=True)
    @patch('bims.utils.gbif_download._species_add_from_dwca', return_value=2, create=True)
    @patch('bims.utils.gbif_download.download_archive', return_value=Path('/tmp/dummy.zip'), create=True)
    @patch('bims.utils.gbif_download.get_ready_download_url', return_value='https://x/d.zip', create=True)
    @patch('bims.utils.gbif_download._submit_with_retry', return_value='dummy', create=True)
    @patch('bims.utils.gbif_download._species_load_set', return_value=(2,1), create=True)
    def test_successful_data_retrieval(
        self,
        _mock_species_load_set,
        _mock_submit_retry,
        _mock_ready,
        _mock_download,
        _mock_add_from_dwca,
        mock_fetch_taxon,
    ):
        boundary = self._make_boundary_with_two_polys()
        harvest_session = HarvestSessionF.create(
            log_file=SimpleUploadedFile("test.log", b"")
        )

        self._prime_resume_meta(
            harvest_session,
            boundary=boundary,
            parent=self.taxon,
            polygon_count=2,
        )

        taxon_1 = TaxonomyF.create()
        taxon_2 = TaxonomyF.create()
        self._seed_sidecar(harvest_session, keys=[1, 2])

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

    @patch('bims.utils.fetch_gbif.fetch_all_species_from_gbif',
           side_effect=Exception("Boom"), create=True)
    @patch('bims.utils.gbif_download._species_add_from_dwca', return_value=2, create=True)
    @patch('bims.utils.gbif_download.download_archive', return_value=Path('/tmp/dummy.zip'), create=True)
    @patch('bims.utils.gbif_download.get_ready_download_url', return_value='https://x/d.zip', create=True)
    @patch('bims.utils.gbif_download._submit_with_retry', return_value='dummy', create=True)
    def test_error_handling_get_species(
        self,
        _mock_submit,
        _mock_ready,
        _mock_download,
        _mock_add_from_dwca,
        _mock_fetch_tax,
    ):
        boundary = self._make_boundary_with_two_polys()
        harvest_session = HarvestSessionF.create(
            log_file=SimpleUploadedFile("test.log", b"")
        )

        self._prime_resume_meta(harvest_session, boundary, self.taxon, polygon_count=2)
        self._seed_sidecar(harvest_session, keys=[1, 2])

        species = find_species_by_area(boundary.id, parent_species=self.taxon, harvest_session=harvest_session)
        self.assertEqual(species, [])

    @patch('bims.utils.gbif_download._species_add_from_dwca', return_value=2, create=True)
    @patch('bims.utils.gbif_download.download_archive', return_value=Path('/tmp/dummy.zip'), create=True)
    @patch('bims.utils.gbif_download.get_ready_download_url', return_value='https://x/d.zip', create=True)
    @patch('bims.utils.gbif_download._submit_with_retry', return_value='dummy', create=True)
    def test_canceled_harvest(
        self,
        _mock_submit,
        _mock_ready,
        _mock_download,
        _mock_add_from_dwca,
    ):
        boundary = self._make_boundary_with_two_polys()

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

        self.assertEqual(species, [])
