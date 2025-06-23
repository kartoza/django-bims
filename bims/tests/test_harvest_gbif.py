import os
import csv
import zipfile
from tempfile import NamedTemporaryFile
from pathlib import Path
from unittest import mock

import requests
from django_tenants.test.cases import FastTenantTestCase
from urllib3.exceptions import ProtocolError

from bims.models import Survey, BiologicalCollectionRecord
from bims.tests.model_factories import (
    BiologicalCollectionRecordF,
    TaxonomyF,
)
from bims.scripts.import_gbif_occurrences import import_gbif_occurrences

# -----------------------------------------------------------------------------
# Helpers & mocks
# -----------------------------------------------------------------------------


def _create_dummy_gbif_zip() -> str:
    """Create a Darwin‑Core zip archive with six occurrences.

    Two rows share identical coordinates so that only five *LocationSite*/Survey
    pairs are produced – mirroring the expectations of the legacy tests.
    """

    header = [
        "gbifID",
        "decimalLongitude",
        "decimalLatitude",
        "coordinateUncertaintyInMeters",
        "eventDate",
        "recordedBy",
        "institutionCode",
        "references",
        "verbatimLocality",
        "locality",
        "species",
        "datasetKey",
        "modified",
        "basisOfRecord",
        "projectId",
        "taxonKey"
    ]

    rows = [
        [
            "2563631087",
            "30",
            "-25",
            "",
            "2021-01-01",
            "Collector F",
            "INST",
            "http://example.org/2563631087",
            "Site F",
            "Site F",
            "Species F",
            "a8503dc0-7226-4ac5-999e-245b458e84b3",
            "2021-01-02",
            "OBSERVATION",
            "",
            "1",
        ],
        [
            "1",
            "30",  # identical coordinates
            "-25",
            "",
            "2021-01-01",
            "Collector A",
            "INST",
            "http://example.org/1",
            "Site A",
            "Site A",
            "Species A",
            "ead9ec8e-b346-4f4f-bad4-7cbaf0e0066f",
            "2021-01-02",
            "OBSERVATION",
            "",
            "1",
        ],
        [
            "2",
            "31",
            "-25",
            "",
            "2021-01-01",
            "Collector B",
            "INST",
            "http://example.org/2",
            "Site B",
            "Site B",
            "Species B",
            "ced0ecb9-19fe-4297-9aa5-2424a687b70c",
            "2021-01-02",
            "OBSERVATION",
            "",
            "1",
        ],
        [
            "3",
            "32",
            "-25",
            "",
            "2021-01-01",
            "Collector C",
            "INST",
            "http://example.org/3",
            "Site C",
            "Site C",
            "Species C",
            "075ae6ac-14c2-4bbf-ac1d-a9a2dd8093db",
            "2021-01-02",
            "OBSERVATION",
            "",
            "1",
        ],
        [
            "4",
            "33",
            "-25",
            "",
            "2021-01-01",
            "Collector D",
            "INST",
            "http://example.org/4",
            "Site D",
            "Site D",
            "Species D",
            "1c15ccaf-25f6-4566-90a8-a5f292e78779",
            "2021-01-02",
            "OBSERVATION",
            "",
            "1",
        ],
        [
            "5",
            "34",
            "-25",
            "",
            "2021-01-01",
            "Collector E",
            "INST",
            "http://example.org/5",
            "Site E",
            "Site E",
            "Species E",
            "087e4051-dcbc-4435-a99e-f6d82f672c82",
            "2021-01-02",
            "OBSERVATION",
            "",
            "1",
        ],
    ]

    with NamedTemporaryFile(delete=False, suffix=".zip") as tmp:
        with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as zf:
            content = "\t".join(header) + "\n" + "\n".join("\t".join(r) for r in rows)
            zf.writestr("occurrence.txt", content)
        return tmp.name


# Dummy replacements for the GBIF helper functions --------------------------------

def _mock_submit_download(*_, **__):
    return "mock-key"


def _mock_get_ready_download_url(*_, **__):
    return "http://example.org/download.zip"


def _mock_download_archive(*_, **__):
    return _create_dummy_gbif_zip()


def _mock_harvest_session_get(*_, **__):
    fake_session = mock.Mock()
    fake_session.id = 1
    fake_session.canceled = False
    return fake_session

# No‑op for dataset look‑ups so the tests stay offline
_noop = lambda *_, **__: None  # noqa: E731 – keep it tiny


# -----------------------------------------------------------------------------
# Test‑case
# -----------------------------------------------------------------------------

@mock.patch("bims.models.location_site.update_location_site_context")
class TestHarvestGbif(FastTenantTestCase):
    """Exercise the GBIF harvest pipeline with fully mocked network helpers."""

    def setUp(self):
        self.taxonomy = TaxonomyF.create(gbif_key=1)
        os.environ.setdefault("GBIF_USERNAME", "user")
        os.environ.setdefault("GBIF_PASSWORD", "pass")

    def tearDown(self):
        BiologicalCollectionRecord.objects.filter(taxonomy=self.taxonomy).delete()
        Survey.objects.filter(biological_collection_record__taxonomy=self.taxonomy).delete()
        self.taxonomy.delete()

    # ------------------------------------------------------------------
    # Success path – first run and idempotency on the second run
    # ------------------------------------------------------------------
    @mock.patch("bims.scripts.import_gbif_occurrences.submit_download", _mock_submit_download)
    @mock.patch("bims.scripts.import_gbif_occurrences.get_ready_download_url", _mock_get_ready_download_url)
    @mock.patch("bims.scripts.import_gbif_occurrences.download_archive", _mock_download_archive)
    @mock.patch("bims.scripts.import_gbif_occurrences.is_canceled", lambda *_: False)
    @mock.patch("bims.scripts.import_gbif_occurrences.create_dataset_from_gbif", _noop)
    @mock.patch("bims.models.HarvestSession.objects.get", _mock_harvest_session_get)
    @mock.patch("bims.scripts.import_gbif_occurrences.preferences")
    def test_harvest_gbif(self, mock_preferences, mock_update_location_context):
        # Configure site preferences (no boundary filtering)
        mock_preferences.SiteSetting.base_country_code = "ZA"
        mock_preferences.SiteSetting.site_boundary = None

        # Sanity: no GBIF data yet
        self.assertEqual(
            BiologicalCollectionRecord.objects.filter(
                owner__username="GBIF",
                taxonomy=self.taxonomy,
                source_reference__source_name="Global Biodiversity Information Facility (GBIF)",
            ).count(),
            0,
        )

        status = import_gbif_occurrences([self.taxonomy.id], session_id=1)
        self.assertTrue(status)

        # Six records, five distinct surveys (two points share identical coords)
        self.assertEqual(
            BiologicalCollectionRecord.objects.filter(
                owner__username="GBIF",
                taxonomy=self.taxonomy,
                source_reference__source_name="Global Biodiversity Information Facility (GBIF)",
            ).count(),
            6,
        )
        self.assertEqual(
            Survey.objects.filter(
                owner__username="GBIF",
                biological_collection_record__taxonomy=self.taxonomy,
                validated=True,
            )
            .distinct()
            .count(),
            5,
        )

        # Second import run must be idempotent
        import_gbif_occurrences([self.taxonomy.id], session_id=1)
        self.assertEqual(
            BiologicalCollectionRecord.objects.filter(
                owner__username="GBIF",
                taxonomy=self.taxonomy,
                source_reference__source_name="Global Biodiversity Information Facility (GBIF)",
            ).count(),
            6,
        )

        mock_update_location_context.assert_called()

    # ------------------------------------------------------------------
    # Incoming data references an upstream_id that already has duplicates
    # ------------------------------------------------------------------
    @mock.patch("bims.scripts.import_gbif_occurrences.submit_download", _mock_submit_download)
    @mock.patch("bims.scripts.import_gbif_occurrences.get_ready_download_url", _mock_get_ready_download_url)
    @mock.patch("bims.scripts.import_gbif_occurrences.download_archive", _mock_download_archive)
    @mock.patch("bims.scripts.import_gbif_occurrences.is_canceled", lambda *_: False)
    @mock.patch("bims.scripts.import_gbif_occurrences.create_dataset_from_gbif", _noop)
    @mock.patch("bims.models.HarvestSession.objects.get", _mock_harvest_session_get)
    @mock.patch("bims.scripts.import_gbif_occurrences.preferences")
    def test_harvest_gbif_multiple_objects_returned(self, mock_preferences, mock_update_location_context):
        mock_preferences.SiteSetting.base_country_code = "ZA"
        mock_preferences.SiteSetting.site_boundary = None

        BiologicalCollectionRecordF.create(upstream_id="2563631087", taxonomy=self.taxonomy)
        BiologicalCollectionRecordF.create(upstream_id="2563631087", taxonomy=self.taxonomy)

        status = import_gbif_occurrences([self.taxonomy.id], session_id=1)
        self.assertTrue(status)

        # Harvester should resolve duplicates – five GBIF rows remain
        self.assertEqual(
            BiologicalCollectionRecord.objects.filter(
                owner__username="GBIF",
                taxonomy=self.taxonomy,
                source_reference__source_name="Global Biodiversity Information Facility (GBIF)",
            ).count(),
            5,
        )
        mock_update_location_context.assert_called()

    # ------------------------------------------------------------------
    # Error handling: HTTPError bubbling up from the GBIF helper
    # ------------------------------------------------------------------
    def _submit_download_http_error(*_, **__):  # pylint: disable=unused-argument
        err = requests.HTTPError("error message")
        err.response = mock.MagicMock()
        err.response.status_code = 404
        raise err

    @mock.patch("bims.utils.gbif_download.submit_download", _submit_download_http_error)
    @mock.patch("bims.models.HarvestSession.objects.get", _mock_harvest_session_get)
    @mock.patch("bims.scripts.import_gbif_occurrences.preferences")
    def test_harvest_gbif_http_error(self, mock_preferences, mock_update_location_context):
        mock_preferences.SiteSetting.base_country_code = "ZA"
        mock_preferences.SiteSetting.site_boundary = None

        status = import_gbif_occurrences([self.taxonomy.id], session_id=1)
        self.assertEqual(status, "Download request failed")

    # ------------------------------------------------------------------
    # Error handling: low‑level connection failures
    # ------------------------------------------------------------------
    def _submit_download_protocol_error(*_, **__):  # pylint: disable=unused-argument
        raise ProtocolError("Connection broken")

    @mock.patch("bims.utils.gbif_download.submit_download", _submit_download_protocol_error)
    @mock.patch("bims.models.HarvestSession.objects.get", _mock_harvest_session_get)
    @mock.patch("bims.scripts.import_gbif_occurrences.preferences")
    def test_harvest_gbif_protocol_error(self, mock_preferences, mock_update_location_context):
        mock_preferences.SiteSetting.base_country_code = "ZA"
        mock_preferences.SiteSetting.site_boundary = None

        status = import_gbif_occurrences([self.taxonomy.id], session_id=1)
        self.assertEqual(status, "Download request failed")
