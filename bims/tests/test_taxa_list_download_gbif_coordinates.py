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

    def test_taxa_list_fields_exist_in_meta(self, mock_update_location_context):
        """Test that GBIF coordinate fields are in the TaxaCSVSerializer Meta fields."""
        fields = TaxaCSVSerializer.Meta.fields
        self.assertIn('gbif_coordinate_uncertainty_m', fields)
        self.assertIn('gbif_coordinate_precision', fields)

    def test_taxa_list_gbif_fields_absent_for_non_sanparks(self, mock_update_location_context):
        """Test that GBIF coordinate columns are absent entirely for non-SanParks sites."""
        site = LocationSite.objects.create(
            geometry_point=Point(25.5, -28.5, srid=4326),
            name="GBIF Test Site",
            location_type=self.location_type,
            coordinate_precision=Decimal("0.00001"),
            coordinate_uncertainty_in_meters=Decimal("30"),
            harvested_from_gbif=True
        )
        BiologicalCollectionRecordF.create(
            site=site,
            taxonomy=self.taxonomy,
            validated=True
        )

        serializer = TaxaCSVSerializer(self.taxonomy)
        data = serializer.data

        self.assertNotIn('gbif_coordinate_uncertainty_m', data)
        self.assertNotIn('gbif_coordinate_precision', data)

    @mock.patch('bims.views.download_csv_taxa_list.is_sanparks_project')
    def test_taxa_list_gbif_fields_with_single_record(
        self, mock_sanparks, mock_update_location_context
    ):
        """Test GBIF coordinate fields in taxa list with a single record (SanParks)."""
        mock_sanparks.return_value = True

        site = LocationSite.objects.create(
            geometry_point=Point(25.5, -28.5, srid=4326),
            name="GBIF Test Site",
            location_type=self.location_type,
            coordinate_precision=Decimal("0.00001"),
            coordinate_uncertainty_in_meters=Decimal("30"),
            harvested_from_gbif=True
        )
        BiologicalCollectionRecordF.create(
            site=site,
            taxonomy=self.taxonomy,
            validated=True
        )

        serializer = TaxaCSVSerializer(self.taxonomy)
        data = serializer.data

        self.assertEqual(data['gbif_coordinate_uncertainty_m'], "30.00")
        self.assertEqual(data['gbif_coordinate_precision'], "0.000010")

    @mock.patch('bims.views.download_csv_taxa_list.is_sanparks_project')
    def test_taxa_list_gbif_fields_with_multiple_records(
        self, mock_sanparks, mock_update_location_context
    ):
        """Test that lowest uncertainty and highest precision are selected (SanParks)."""
        mock_sanparks.return_value = True

        site1 = LocationSite.objects.create(
            geometry_point=Point(25.5, -28.5, srid=4326),
            name="GBIF Site 1",
            location_type=self.location_type,
            coordinate_precision=Decimal("0.00001"),
            coordinate_uncertainty_in_meters=Decimal("50"),
            harvested_from_gbif=True
        )
        site2 = LocationSite.objects.create(
            geometry_point=Point(26.5, -29.5, srid=4326),
            name="GBIF Site 2",
            location_type=self.location_type,
            coordinate_precision=Decimal("0.01667"),
            coordinate_uncertainty_in_meters=Decimal("30"),
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

        for site in [site1, site2, site3]:
            BiologicalCollectionRecordF.create(
                site=site,
                taxonomy=self.taxonomy,
                validated=True
            )

        serializer = TaxaCSVSerializer(self.taxonomy)
        data = serializer.data

        self.assertEqual(data['gbif_coordinate_uncertainty_m'], "30.00")
        self.assertEqual(data['gbif_coordinate_precision'], "0.000010")

    @mock.patch('bims.views.download_csv_taxa_list.is_sanparks_project')
    def test_taxa_list_gbif_fields_ignores_non_gbif_sites(
        self, mock_sanparks, mock_update_location_context
    ):
        """Test that non-GBIF sites are ignored in taxa list (SanParks)."""
        mock_sanparks.return_value = True

        gbif_site = LocationSite.objects.create(
            geometry_point=Point(25.5, -28.5, srid=4326),
            name="GBIF Site",
            location_type=self.location_type,
            coordinate_precision=Decimal("0.00001"),
            coordinate_uncertainty_in_meters=Decimal("30"),
            harvested_from_gbif=True
        )
        manual_site = LocationSite.objects.create(
            geometry_point=Point(26.5, -29.5, srid=4326),
            name="Manual Site",
            location_type=self.location_type,
            coordinate_precision=Decimal("0.000001"),
            coordinate_uncertainty_in_meters=Decimal("10"),
            harvested_from_gbif=False
        )

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

        serializer = TaxaCSVSerializer(self.taxonomy)
        data = serializer.data

        self.assertEqual(data['gbif_coordinate_uncertainty_m'], "30.00")
        self.assertEqual(data['gbif_coordinate_precision'], "0.000010")

    @mock.patch('bims.views.download_csv_taxa_list.is_sanparks_project')
    def test_taxa_list_gbif_fields_with_no_gbif_records(
        self, mock_sanparks, mock_update_location_context
    ):
        """Test that empty strings are returned when no GBIF records exist (SanParks)."""
        mock_sanparks.return_value = True

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

        serializer = TaxaCSVSerializer(self.taxonomy)
        data = serializer.data

        self.assertEqual(data['gbif_coordinate_uncertainty_m'], "")
        self.assertEqual(data['gbif_coordinate_precision'], "")

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

    @mock.patch('bims.views.download_csv_taxa_list.is_sanparks_project')
    @mock.patch('bims.views.download_csv_taxa_list.apply_gbif_record_threshold')
    def test_taxa_list_10000_threshold_for_uncertainty(
        self, mock_apply_threshold, mock_sanparks, mock_update_location_context
    ):
        """Test that the 10,000 record threshold is applied for coordinate uncertainty."""
        mock_sanparks.return_value = True

        site1 = LocationSite.objects.create(
            geometry_point=Point(25.5, -28.5, srid=4326),
            name="GBIF Site 1",
            location_type=self.location_type,
            coordinate_precision=Decimal("0.00001"),
            coordinate_uncertainty_in_meters=Decimal("100"),
            harvested_from_gbif=True
        )
        site2 = LocationSite.objects.create(
            geometry_point=Point(26.5, -29.5, srid=4326),
            name="GBIF Site 2",
            location_type=self.location_type,
            coordinate_precision=Decimal("0.00001"),
            coordinate_uncertainty_in_meters=Decimal("30"),
            harvested_from_gbif=True
        )

        BiologicalCollectionRecordF.create(
            site=site1,
            taxonomy=self.taxonomy,
            validated=True
        )
        BiologicalCollectionRecordF.create(
            site=site2,
            taxonomy=self.taxonomy,
            validated=True
        )

        def mock_threshold_side_effect(queryset, threshold=10000, limit=100):
            return queryset.filter(site=site1)

        mock_apply_threshold.side_effect = mock_threshold_side_effect

        serializer = TaxaCSVSerializer(self.taxonomy)
        data = serializer.data

        self.assertEqual(mock_apply_threshold.call_count, 2)
        self.assertEqual(data['gbif_coordinate_uncertainty_m'], "100.00")

    @mock.patch('bims.views.download_csv_taxa_list.is_sanparks_project')
    @mock.patch('bims.views.download_csv_taxa_list.apply_gbif_record_threshold')
    def test_taxa_list_10000_threshold_for_precision(
        self, mock_apply_threshold, mock_sanparks, mock_update_location_context
    ):
        """Test that the 10,000 record threshold is applied for coordinate precision."""
        mock_sanparks.return_value = True

        site1 = LocationSite.objects.create(
            geometry_point=Point(25.5, -28.5, srid=4326),
            name="GBIF Site 1",
            location_type=self.location_type,
            coordinate_precision=Decimal("0.01667"),
            coordinate_uncertainty_in_meters=Decimal("30"),
            harvested_from_gbif=True
        )
        site2 = LocationSite.objects.create(
            geometry_point=Point(26.5, -29.5, srid=4326),
            name="GBIF Site 2",
            location_type=self.location_type,
            coordinate_precision=Decimal("0.00001"),
            coordinate_uncertainty_in_meters=Decimal("30"),
            harvested_from_gbif=True
        )

        BiologicalCollectionRecordF.create(
            site=site1,
            taxonomy=self.taxonomy,
            validated=True
        )
        BiologicalCollectionRecordF.create(
            site=site2,
            taxonomy=self.taxonomy,
            validated=True
        )

        def mock_threshold_side_effect(queryset, threshold=10000, limit=100):
            return queryset.filter(site=site1)[:1]

        mock_apply_threshold.side_effect = mock_threshold_side_effect

        serializer = TaxaCSVSerializer(self.taxonomy)
        data = serializer.data

        self.assertEqual(mock_apply_threshold.call_count, 2)
        self.assertEqual(data['gbif_coordinate_precision'], "0.016670")

    @mock.patch('bims.views.download_csv_taxa_list.is_sanparks_project')
    @mock.patch('bims.views.download_csv_taxa_list.apply_gbif_record_threshold')
    def test_taxa_list_no_threshold_under_10000(
        self, mock_apply_threshold, mock_sanparks, mock_update_location_context
    ):
        """Test that all records are used when count is under 10,000."""
        mock_sanparks.return_value = True

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
            coordinate_precision=Decimal("0.00001"),
            coordinate_uncertainty_in_meters=Decimal("30"),
            harvested_from_gbif=True
        )

        BiologicalCollectionRecordF.create(
            site=site1,
            taxonomy=self.taxonomy,
            validated=True
        )
        BiologicalCollectionRecordF.create(
            site=site2,
            taxonomy=self.taxonomy,
            validated=True
        )

        mock_apply_threshold.side_effect = lambda queryset, **kwargs: queryset

        serializer = TaxaCSVSerializer(self.taxonomy)
        data = serializer.data

        self.assertEqual(mock_apply_threshold.call_count, 2)
        self.assertEqual(data['gbif_coordinate_uncertainty_m'], "30.00")
        self.assertEqual(data['gbif_coordinate_precision'], "0.000010")
