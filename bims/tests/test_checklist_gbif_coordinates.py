"""Tests for GBIF coordinate fields in checklist downloads."""
from decimal import Decimal
from unittest import mock

from django.contrib.gis.geos import Point
from django_tenants.test.cases import FastTenantTestCase

from bims.models import LocationSite, LocationType
from bims.serializers.checklist_serializer import ChecklistSerializer
from bims.tests.model_factories import (
    TaxonomyF,
    BiologicalCollectionRecordF,
)


@mock.patch("bims.models.location_site.update_location_site_context")
class TestChecklistGBIFCoordinates(FastTenantTestCase):
    """Test GBIF coordinate fields in checklist."""

    def setUp(self):
        """Set up test fixtures."""
        self.taxonomy = TaxonomyF.create(
            canonical_name="Test species",
            rank="SPECIES",
            scientific_name="Test species Author"
        )
        self.location_type, _ = LocationType.objects.get_or_create(
            name="PointObservation",
            allowed_geometry="POINT"
        )

    def tearDown(self):
        """Clean up test data."""
        LocationSite.objects.all().delete()
        self.taxonomy.delete()

    def test_checklist_gbif_fields_with_single_record(self, mock_update_location_context):
        """Test GBIF coordinate fields in checklist with a single record."""
        # Create a GBIF-harvested site
        site = LocationSite.objects.create(
            geometry_point=Point(25.5, -28.5, srid=4326),
            name="GBIF Test Site",
            location_type=self.location_type,
            coordinate_precision=Decimal("0.00001"),
            coordinate_uncertainty_in_meters=Decimal("30"),
            harvested_from_gbif=True
        )

        # Create a biological record
        record = BiologicalCollectionRecordF.create(
            site=site,
            taxonomy=self.taxonomy,
            validated=True
        )

        # Serialize the taxonomy with collection records context
        serializer = ChecklistSerializer(
            self.taxonomy,
            context={'collection_records': type(record).objects.filter(id=record.id)}
        )
        data = serializer.data

        # Check the GBIF coordinate fields
        self.assertEqual(data['gbif_coordinate_uncertainty_m'], "30.00")
        self.assertEqual(data['gbif_coordinate_precision'], "0.000010")

    def test_checklist_gbif_fields_with_multiple_records(self, mock_update_location_context):
        """Test that lowest uncertainty and highest precision are selected in checklist."""
        # Create multiple GBIF-harvested sites with different coordinate values
        site1 = LocationSite.objects.create(
            geometry_point=Point(25.5, -28.5, srid=4326),
            name="GBIF Site 1",
            location_type=self.location_type,
            coordinate_precision=Decimal("0.00001"),  # Highest precision
            coordinate_uncertainty_in_meters=Decimal("50"),
            harvested_from_gbif=True
        )

        site2 = LocationSite.objects.create(
            geometry_point=Point(26.5, -29.5, srid=4326),
            name="GBIF Site 2",
            location_type=self.location_type,
            coordinate_precision=Decimal("0.01667"),  # Lower precision
            coordinate_uncertainty_in_meters=Decimal("30"),  # Lowest uncertainty
            harvested_from_gbif=True
        )

        site3 = LocationSite.objects.create(
            geometry_point=Point(27.5, -30.5, srid=4326),
            name="GBIF Site 3",
            location_type=self.location_type,
            coordinate_precision=Decimal("0.000278"),
            coordinate_uncertainty_in_meters=Decimal("100"),
            harvested_from_gbif=True
        )

        # Create biological records for all sites
        records = []
        for site in [site1, site2, site3]:
            records.append(BiologicalCollectionRecordF.create(
                site=site,
                taxonomy=self.taxonomy,
                validated=True
            ))

        # Serialize the taxonomy
        serializer = ChecklistSerializer(
            self.taxonomy,
            context={'collection_records': type(records[0]).objects.filter(
                id__in=[r.id for r in records]
            )}
        )
        data = serializer.data

        # Should show the lowest uncertainty (30) and highest precision (0.00001)
        self.assertEqual(data['gbif_coordinate_uncertainty_m'], "30.00")
        self.assertEqual(data['gbif_coordinate_precision'], "0.000010")

    def test_checklist_gbif_fields_ignores_non_gbif_sites(self, mock_update_location_context):
        """Test that non-GBIF sites are ignored in checklist."""
        # Create a GBIF site
        gbif_site = LocationSite.objects.create(
            geometry_point=Point(25.5, -28.5, srid=4326),
            name="GBIF Site",
            location_type=self.location_type,
            coordinate_precision=Decimal("0.00001"),
            coordinate_uncertainty_in_meters=Decimal("30"),
            harvested_from_gbif=True
        )

        # Create a non-GBIF site with better values (should be ignored)
        manual_site = LocationSite.objects.create(
            geometry_point=Point(26.5, -29.5, srid=4326),
            name="Manual Site",
            location_type=self.location_type,
            coordinate_precision=Decimal("0.000001"),  # Better precision
            coordinate_uncertainty_in_meters=Decimal("10"),  # Lower uncertainty
            harvested_from_gbif=False  # Not from GBIF
        )

        # Create records for both sites
        records = [
            BiologicalCollectionRecordF.create(
                site=gbif_site,
                taxonomy=self.taxonomy,
                validated=True
            ),
            BiologicalCollectionRecordF.create(
                site=manual_site,
                taxonomy=self.taxonomy,
                validated=True
            )
        ]

        # Serialize the taxonomy
        serializer = ChecklistSerializer(
            self.taxonomy,
            context={'collection_records': type(records[0]).objects.filter(
                id__in=[r.id for r in records]
            )}
        )
        data = serializer.data

        # Should only use GBIF site values
        self.assertEqual(data['gbif_coordinate_uncertainty_m'], "30.00")
        self.assertEqual(data['gbif_coordinate_precision'], "0.000010")

    def test_checklist_gbif_fields_with_no_gbif_records(self, mock_update_location_context):
        """Test that empty strings are returned when no GBIF records exist in checklist."""
        # Create only non-GBIF records
        site = LocationSite.objects.create(
            geometry_point=Point(25.5, -28.5, srid=4326),
            name="Manual Site",
            location_type=self.location_type,
            harvested_from_gbif=False
        )

        record = BiologicalCollectionRecordF.create(
            site=site,
            taxonomy=self.taxonomy,
            validated=True
        )

        # Serialize the taxonomy
        serializer = ChecklistSerializer(
            self.taxonomy,
            context={'collection_records': type(record).objects.filter(id=record.id)}
        )
        data = serializer.data

        # Should return empty strings
        self.assertEqual(data['gbif_coordinate_uncertainty_m'], "")
        self.assertEqual(data['gbif_coordinate_precision'], "")

    def test_checklist_fields_exist_in_meta(self, mock_update_location_context):
        """Test that GBIF coordinate fields are in the serializer Meta fields."""
        fields = ChecklistSerializer.Meta.fields
        self.assertIn('gbif_coordinate_uncertainty_m', fields)
        self.assertIn('gbif_coordinate_precision', fields)
