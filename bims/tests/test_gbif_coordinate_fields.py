"""Tests for GBIF coordinate precision and uncertainty field handling."""
import os
import uuid
from decimal import Decimal
from unittest import mock
from datetime import datetime

from django.contrib.gis.geos import Point
from django_tenants.test.cases import FastTenantTestCase

from bims.models import LocationSite, LocationType, BiologicalCollectionRecord
from bims.scripts.import_gbif_occurrences import process_gbif_row
from bims.tests.model_factories import (
    TaxonomyF,
    UserF,
    SourceReferenceDatabaseF,
    TaxonGroupF,
)


# Mock the dataset creation function
def _mock_create_dataset(*args, **kwargs):
    """No-op for dataset creation to keep tests offline."""
    pass


@mock.patch("bims.models.location_site.update_location_site_context")
class TestGbifCoordinateFields(FastTenantTestCase):
    """Test coordinate precision and uncertainty fields from GBIF."""

    def setUp(self):
        """Set up test fixtures."""
        self.taxonomy = TaxonomyF.create(gbif_key=12345)
        self.owner = UserF.create(username="test_user")
        self.source_reference = SourceReferenceDatabaseF.create(
            source_name="Test Source"
        )
        self.taxon_group = TaxonGroupF.create()
        self.source_collection = "test_collection"

        # Mock log function
        self.log_messages = []
        self.log = lambda msg: self.log_messages.append(msg)

    def tearDown(self):
        """Clean up test data."""
        BiologicalCollectionRecord.objects.all().delete()
        LocationSite.objects.all().delete()
        self.taxonomy.delete()
        self.owner.delete()
        self.source_reference.delete()
        self.taxon_group.delete()

    @mock.patch("bims.scripts.import_gbif_occurrences.create_dataset_from_gbif", _mock_create_dataset)
    def test_new_site_with_coordinate_fields(self, mock_update_location_context):
        """Test that new sites created from GBIF have coordinate fields populated."""
        row = {
            "gbifID": "test123",
            "decimalLongitude": "25.5",
            "decimalLatitude": "-28.5",
            "coordinateUncertaintyInMeters": "30",
            "coordinatePrecision": "0.00001",
            "eventDate": "2021-01-01",
            "recordedBy": "Test Collector",
            "institutionCode": "TEST",
            "references": "http://example.org/test",
            "locality": "Test Location",
            "species": "Test species",
            "datasetKey": str(uuid.uuid4()),
            "taxonKey": "12345",
            "basisOfRecord": "OBSERVATION",
        }

        record, processed = process_gbif_row(
            row=row,
            owner=self.owner,
            source_reference=self.source_reference,
            source_collection=self.source_collection,
            harvest_session=None,
            taxon_group=self.taxon_group,
            log=self.log,
        )

        self.assertTrue(processed)
        self.assertIsNotNone(record)

        # Verify the LocationSite was created with correct fields
        site = LocationSite.objects.filter(
            geometry_point__equals=Point(25.5, -28.5, srid=4326)
        ).first()

        self.assertIsNotNone(site)
        self.assertEqual(site.coordinate_precision, Decimal("0.00001"))
        self.assertEqual(site.coordinate_uncertainty_in_meters, Decimal("30"))
        self.assertTrue(site.harvested_from_gbif)

    @mock.patch("bims.scripts.import_gbif_occurrences.create_dataset_from_gbif", _mock_create_dataset)
    def test_existing_site_without_coordinate_fields_gets_updated(
        self, mock_update_location_context
    ):
        """Test that existing sites without coordinate fields get them populated."""
        # Create a site without coordinate fields (legacy GBIF harvest)
        location_type, _ = LocationType.objects.get_or_create(
            name="PointObservation", allowed_geometry="POINT"
        )
        existing_site = LocationSite.objects.create(
            geometry_point=Point(25.5, -28.5, srid=4326),
            name="Existing Site",
            location_type=location_type,
            site_description="Legacy site",
            coordinate_precision=None,
            coordinate_uncertainty_in_meters=None,
            harvested_from_gbif=False,
        )

        row = {
            "gbifID": "test124",
            "decimalLongitude": "25.5",
            "decimalLatitude": "-28.5",
            "coordinateUncertaintyInMeters": "50",
            "coordinatePrecision": "0.000278",
            "eventDate": "2021-01-01",
            "recordedBy": "Test Collector 2",
            "institutionCode": "TEST",
            "references": "http://example.org/test2",
            "locality": "Test Location 2",
            "species": "Test species 2",
            "datasetKey": str(uuid.uuid4()),
            "taxonKey": "12345",
            "basisOfRecord": "OBSERVATION",
        }

        record, processed = process_gbif_row(
            row=row,
            owner=self.owner,
            source_reference=self.source_reference,
            source_collection=self.source_collection,
            harvest_session=None,
            taxon_group=self.taxon_group,
            log=self.log,
        )

        self.assertTrue(processed)

        # Refresh the existing site from DB
        existing_site.refresh_from_db()

        # Verify the fields were updated
        self.assertEqual(existing_site.coordinate_precision, Decimal("0.000278"))
        self.assertEqual(
            existing_site.coordinate_uncertainty_in_meters, Decimal("50")
        )
        self.assertTrue(existing_site.harvested_from_gbif)

    @mock.patch("bims.scripts.import_gbif_occurrences.create_dataset_from_gbif", _mock_create_dataset)
    def test_existing_site_with_coordinate_fields_not_overwritten(
        self, mock_update_location_context
    ):
        """Test that existing sites with coordinate fields don't get overwritten."""
        # Create a site with coordinate fields already populated
        location_type, _ = LocationType.objects.get_or_create(
            name="PointObservation", allowed_geometry="POINT"
        )
        existing_site = LocationSite.objects.create(
            geometry_point=Point(25.5, -28.5, srid=4326),
            name="Existing Site with Data",
            location_type=location_type,
            site_description="Site with existing coordinate data",
            coordinate_precision=Decimal("0.01667"),
            coordinate_uncertainty_in_meters=Decimal("100"),
            harvested_from_gbif=True,
        )

        original_precision = existing_site.coordinate_precision
        original_uncertainty = existing_site.coordinate_uncertainty_in_meters

        row = {
            "gbifID": "test125",
            "decimalLongitude": "25.5",
            "decimalLatitude": "-28.5",
            "coordinateUncertaintyInMeters": "30",
            "coordinatePrecision": "0.00001",
            "eventDate": "2021-01-01",
            "recordedBy": "Test Collector 3",
            "institutionCode": "TEST",
            "references": "http://example.org/test3",
            "locality": "Test Location 3",
            "species": "Test species 3",
            "datasetKey": str(uuid.uuid4()),
            "taxonKey": "12345",
            "basisOfRecord": "OBSERVATION",
        }

        record, processed = process_gbif_row(
            row=row,
            owner=self.owner,
            source_reference=self.source_reference,
            source_collection=self.source_collection,
            harvest_session=None,
            taxon_group=self.taxon_group,
            log=self.log,
        )

        self.assertTrue(processed)

        # Refresh the existing site from DB
        existing_site.refresh_from_db()

        # Verify the fields were NOT overwritten
        self.assertEqual(existing_site.coordinate_precision, original_precision)
        self.assertEqual(
            existing_site.coordinate_uncertainty_in_meters, original_uncertainty
        )

    @mock.patch("bims.scripts.import_gbif_occurrences.create_dataset_from_gbif", _mock_create_dataset)
    def test_site_with_missing_coordinate_precision(self, mock_update_location_context):
        """Test handling of GBIF data without coordinatePrecision field."""
        row = {
            "gbifID": "test126",
            "decimalLongitude": "26.5",
            "decimalLatitude": "-29.5",
            "coordinateUncertaintyInMeters": "71",
            "coordinatePrecision": "",  # Empty precision
            "eventDate": "2021-01-01",
            "recordedBy": "Test Collector 4",
            "institutionCode": "TEST",
            "references": "http://example.org/test4",
            "locality": "Test Location 4",
            "species": "Test species 4",
            "datasetKey": str(uuid.uuid4()),
            "taxonKey": "12345",
            "basisOfRecord": "OBSERVATION",
        }

        record, processed = process_gbif_row(
            row=row,
            owner=self.owner,
            source_reference=self.source_reference,
            source_collection=self.source_collection,
            harvest_session=None,
            taxon_group=self.taxon_group,
            log=self.log,
        )

        self.assertTrue(processed)
        self.assertIsNotNone(record)

        # Verify the LocationSite was created with uncertainty but no precision
        site = LocationSite.objects.filter(
            geometry_point__equals=Point(26.5, -29.5, srid=4326)
        ).first()

        self.assertIsNotNone(site)
        self.assertIsNone(site.coordinate_precision)
        self.assertEqual(site.coordinate_uncertainty_in_meters, Decimal("71"))
        self.assertTrue(site.harvested_from_gbif)

    @mock.patch("bims.scripts.import_gbif_occurrences.create_dataset_from_gbif", _mock_create_dataset)
    def test_site_with_missing_coordinate_uncertainty(
        self, mock_update_location_context
    ):
        """Test handling of GBIF data without coordinateUncertaintyInMeters field."""
        row = {
            "gbifID": "test127",
            "decimalLongitude": "27.5",
            "decimalLatitude": "-30.5",
            "coordinateUncertaintyInMeters": "",  # Empty uncertainty
            "coordinatePrecision": "1.0",
            "eventDate": "2021-01-01",
            "recordedBy": "Test Collector 5",
            "institutionCode": "TEST",
            "references": "http://example.org/test5",
            "locality": "Test Location 5",
            "species": "Test species 5",
            "datasetKey": str(uuid.uuid4()),
            "taxonKey": "12345",
            "basisOfRecord": "OBSERVATION",
        }

        record, processed = process_gbif_row(
            row=row,
            owner=self.owner,
            source_reference=self.source_reference,
            source_collection=self.source_collection,
            harvest_session=None,
            taxon_group=self.taxon_group,
            log=self.log,
        )

        self.assertTrue(processed)
        self.assertIsNotNone(record)

        # Verify the LocationSite was created with precision but no uncertainty
        site = LocationSite.objects.filter(
            geometry_point__equals=Point(27.5, -30.5, srid=4326)
        ).first()

        self.assertIsNotNone(site)
        self.assertEqual(site.coordinate_precision, Decimal("1.0"))
        self.assertIsNone(site.coordinate_uncertainty_in_meters)
        self.assertTrue(site.harvested_from_gbif)
