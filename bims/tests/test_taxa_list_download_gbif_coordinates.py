"""Tests for GBIF coordinate fields in taxa list downloads."""
from decimal import Decimal
from unittest import mock

from django.contrib.gis.geos import Point
from django_tenants.test.cases import FastTenantTestCase
from preferences import preferences

from bims.models import (
    LocationSite,
    LocationType,
    BiologicalCollectionRecord,
    Invasion,
)
from bims.views.download_csv_taxa_list import TaxaCSVSerializer
from bims.tests.model_factories import (
    TaxonomyF,
    BiologicalCollectionRecordF,
)


@mock.patch("bims.models.location_site.update_location_site_context")
class TestTaxaListDownloadGBIFCoordinates(FastTenantTestCase):
    """Test GBIF coordinate fields in taxa list downloads."""

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
        BiologicalCollectionRecord.objects.all().delete()
        LocationSite.objects.all().delete()
        Invasion.objects.all().delete()
        self.taxonomy.delete()

    def test_taxa_list_gbif_fields_with_single_record(self, mock_update_location_context):
        """Test GBIF coordinate fields in taxa list with a single record."""
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
        BiologicalCollectionRecordF.create(
            site=site,
            taxonomy=self.taxonomy,
            validated=True
        )

        # Serialize the taxonomy
        serializer = TaxaCSVSerializer(self.taxonomy)
        data = serializer.data

        # Check the GBIF coordinate fields
        self.assertEqual(data['gbif_coordinate_uncertainty_m'], "30.00")
        self.assertEqual(data['gbif_coordinate_precision'], "0.000010")

    def test_taxa_list_gbif_fields_with_multiple_records(self, mock_update_location_context):
        """Test that lowest uncertainty and highest precision are selected in taxa list."""
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
        for site in [site1, site2, site3]:
            BiologicalCollectionRecordF.create(
                site=site,
                taxonomy=self.taxonomy,
                validated=True
            )

        # Serialize the taxonomy
        serializer = TaxaCSVSerializer(self.taxonomy)
        data = serializer.data

        # Should show the lowest uncertainty (30) and highest precision (0.00001)
        self.assertEqual(data['gbif_coordinate_uncertainty_m'], "30.00")
        self.assertEqual(data['gbif_coordinate_precision'], "0.000010")

    def test_taxa_list_gbif_fields_ignores_non_gbif_sites(self, mock_update_location_context):
        """Test that non-GBIF sites are ignored in taxa list."""
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
        BiologicalCollectionRecordF.create(
            site=gbif_site,
            taxonomy=self.taxonomy,
            validated=True
        )
        BiologicalCollectionRecordF.create(
            site=manual_site,
            taxonomy=self.taxonomy,
            validated=True
        )

        # Serialize the taxonomy
        serializer = TaxaCSVSerializer(self.taxonomy)
        data = serializer.data

        # Should only use GBIF site values
        self.assertEqual(data['gbif_coordinate_uncertainty_m'], "30.00")
        self.assertEqual(data['gbif_coordinate_precision'], "0.000010")

    def test_taxa_list_gbif_fields_with_no_gbif_records(self, mock_update_location_context):
        """Test that empty strings are returned when no GBIF records exist in taxa list."""
        # Create only non-GBIF records
        site = LocationSite.objects.create(
            geometry_point=Point(25.5, -28.5, srid=4326),
            name="Manual Site",
            location_type=self.location_type,
            harvested_from_gbif=False
        )

        BiologicalCollectionRecordF.create(
            site=site,
            taxonomy=self.taxonomy,
            validated=True
        )

        # Serialize the taxonomy
        serializer = TaxaCSVSerializer(self.taxonomy)
        data = serializer.data

        # Should return empty strings
        self.assertEqual(data['gbif_coordinate_uncertainty_m'], "")
        self.assertEqual(data['gbif_coordinate_precision'], "")

    def test_taxa_list_fields_exist_in_meta(self, mock_update_location_context):
        """Test that GBIF coordinate fields are in the TaxaCSVSerializer Meta fields."""
        fields = TaxaCSVSerializer.Meta.fields
        self.assertIn('gbif_coordinate_uncertainty_m', fields)
        self.assertIn('gbif_coordinate_precision', fields)

    @mock.patch("bims.views.download_csv_taxa_list.preferences")
    def test_sanparks_nemba_status_defaults_to_empty(
        self, mock_preferences, mock_update_location_context
    ):
        """Sanparks master list should display empty when invasion missing."""
        mock_preferences.SiteSetting.project_name = "sanparks"
        serializer = TaxaCSVSerializer(self.taxonomy)
        self.assertEqual(serializer.data['invasion'], '')

    @mock.patch("bims.views.download_csv_taxa_list.preferences")
    def test_sanparks_nemba_status_limited_to_allowed_values(
        self, mock_preferences, mock_update_location_context
    ):
        """Sanparks master list should normalize invasion values to allowed statuses."""
        mock_preferences.SiteSetting.project_name = "sanparks"
        invalid_invasion = Invasion.objects.create(category="Alien invasive")
        self.taxonomy.invasion = invalid_invasion
        self.taxonomy.save()
        serializer = TaxaCSVSerializer(self.taxonomy)
        self.assertEqual(serializer.data['invasion'], '')

        allowed_invasion = Invasion.objects.create(category="Category 1b invasive")
        self.taxonomy.invasion = allowed_invasion
        self.taxonomy.save()
        serializer = TaxaCSVSerializer(self.taxonomy)
        self.assertEqual(serializer.data['invasion'], 'Category 1b invasive')

    @mock.patch('bims.views.download_csv_taxa_list.apply_gbif_record_threshold')
    def test_taxa_list_10000_threshold_for_uncertainty(
        self, mock_apply_threshold, mock_update_location_context
    ):
        """Test that the 10,000 record threshold is applied for coordinate uncertainty."""
        # Create a GBIF site with specific uncertainty
        site1 = LocationSite.objects.create(
            geometry_point=Point(25.5, -28.5, srid=4326),
            name="GBIF Site 1",
            location_type=self.location_type,
            coordinate_precision=Decimal("0.00001"),
            coordinate_uncertainty_in_meters=Decimal("100"),  # Higher uncertainty
            harvested_from_gbif=True
        )

        site2 = LocationSite.objects.create(
            geometry_point=Point(26.5, -29.5, srid=4326),
            name="GBIF Site 2",
            location_type=self.location_type,
            coordinate_precision=Decimal("0.00001"),
            coordinate_uncertainty_in_meters=Decimal("30"),  # Lower uncertainty
            harvested_from_gbif=True
        )

        # Create actual records
        record1 = BiologicalCollectionRecordF.create(
            site=site1,
            taxonomy=self.taxonomy,
            validated=True
        )
        record2 = BiologicalCollectionRecordF.create(
            site=site2,
            taxonomy=self.taxonomy,
            validated=True
        )

        # Mock apply_gbif_record_threshold to return a limited queryset
        # that only includes the first record (simulating the threshold being applied)
        def mock_threshold_side_effect(queryset, threshold=10000, limit=100):
            # Return only the first record to simulate limiting
            return queryset.filter(site=site1)

        mock_apply_threshold.side_effect = mock_threshold_side_effect

        # Serialize the taxonomy
        serializer = TaxaCSVSerializer(self.taxonomy)
        data = serializer.data

        # Verify that apply_gbif_record_threshold was called twice (once for each field)
        self.assertEqual(mock_apply_threshold.call_count, 2)

        # The result should be from the limited set (only site1 with higher uncertainty)
        self.assertEqual(data['gbif_coordinate_uncertainty_m'], "100.00")

    @mock.patch('bims.views.download_csv_taxa_list.apply_gbif_record_threshold')
    def test_taxa_list_10000_threshold_for_precision(
        self, mock_apply_threshold, mock_update_location_context
    ):
        """Test that the 10,000 record threshold is applied for coordinate precision."""
        # Create a GBIF site with specific precision
        site1 = LocationSite.objects.create(
            geometry_point=Point(25.5, -28.5, srid=4326),
            name="GBIF Site 1",
            location_type=self.location_type,
            coordinate_precision=Decimal("0.01667"),  # Lower precision
            coordinate_uncertainty_in_meters=Decimal("30"),
            harvested_from_gbif=True
        )

        site2 = LocationSite.objects.create(
            geometry_point=Point(26.5, -29.5, srid=4326),
            name="GBIF Site 2",
            location_type=self.location_type,
            coordinate_precision=Decimal("0.00001"),  # Higher precision
            coordinate_uncertainty_in_meters=Decimal("30"),
            harvested_from_gbif=True
        )

        # Create actual records
        record1 = BiologicalCollectionRecordF.create(
            site=site1,
            taxonomy=self.taxonomy,
            validated=True
        )
        record2 = BiologicalCollectionRecordF.create(
            site=site2,
            taxonomy=self.taxonomy,
            validated=True
        )

        # Mock apply_gbif_record_threshold to return a limited queryset
        # that only includes the first record (simulating the threshold being applied)
        def mock_threshold_side_effect(queryset, threshold=10000, limit=100):
            # Return only the first record to simulate limiting
            return queryset.filter(site=site1)[:1]

        mock_apply_threshold.side_effect = mock_threshold_side_effect

        # Serialize the taxonomy
        serializer = TaxaCSVSerializer(self.taxonomy)
        data = serializer.data

        # Verify that apply_gbif_record_threshold was called twice (once for each field)
        self.assertEqual(mock_apply_threshold.call_count, 2)

        # The result should be from the limited set (only site1 with lower precision)
        self.assertEqual(data['gbif_coordinate_precision'], "0.016670")

    @mock.patch('bims.views.download_csv_taxa_list.apply_gbif_record_threshold')
    def test_taxa_list_no_threshold_under_10000(
        self, mock_apply_threshold, mock_update_location_context
    ):
        """Test that all records are used when count is under 10,000."""
        # Create GBIF sites
        site1 = LocationSite.objects.create(
            geometry_point=Point(25.5, -28.5, srid=4326),
            name="GBIF Site 1",
            location_type=self.location_type,
            coordinate_precision=Decimal("0.01667"),
            coordinate_uncertainty_in_meters=Decimal("100"),
            harvested_from_gbif=True
        )

        site2 = LocationSite.objects.create(
            geometry_point=Point(26.5, -29.5, srid=4326),
            name="GBIF Site 2",
            location_type=self.location_type,
            coordinate_precision=Decimal("0.00001"),  # Best precision
            coordinate_uncertainty_in_meters=Decimal("30"),  # Best uncertainty
            harvested_from_gbif=True
        )

        # Create actual records
        record1 = BiologicalCollectionRecordF.create(
            site=site1,
            taxonomy=self.taxonomy,
            validated=True
        )
        record2 = BiologicalCollectionRecordF.create(
            site=site2,
            taxonomy=self.taxonomy,
            validated=True
        )

        # Mock apply_gbif_record_threshold to pass through the queryset unchanged
        # (simulating that the threshold is not exceeded)
        mock_apply_threshold.side_effect = lambda queryset, **kwargs: queryset

        # Serialize the taxonomy
        serializer = TaxaCSVSerializer(self.taxonomy)
        data = serializer.data

        # Verify that apply_gbif_record_threshold was called twice (once for each field)
        self.assertEqual(mock_apply_threshold.call_count, 2)

        # Results should be from all records (best values)
        self.assertEqual(data['gbif_coordinate_uncertainty_m'], "30.00")
        self.assertEqual(data['gbif_coordinate_precision'], "0.000010")
