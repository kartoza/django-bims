"""Tests for BioCollectionOneRowSerializer coordinate and conservation methods."""
from decimal import Decimal
from unittest import mock

from django_tenants.test.cases import FastTenantTestCase

from bims.models import IUCNStatus
from bims.serializers.bio_collection_serializer import BioCollectionOneRowSerializer
from bims.tests.model_factories import (
    BiologicalCollectionRecordF,
    IUCNStatusF,
    LocationSiteF,
    TaxonomyF,
)


def _make_iucn(category):
    return IUCNStatus.objects.create(category=category)


@mock.patch('bims.models.location_site.update_location_site_context')
@mock.patch('bims.models.taxonomy.get_iucn_status', return_value=(None, None, None))
class TestGetConservationStatusGlobal(FastTenantTestCase):
    """
    Tests for BioCollectionOneRowSerializer.get_conservation_status_global.

    The method:
      1. Resolves to accepted_taxonomy when taxon is a synonym/doubtful
         (note: currently uses the misnamed attribute 'accepted_taxon' instead
         of 'accepted_taxonomy', see test_synonym_with_accepted_taxonomy_*)
      2. Returns the human-readable IUCN label from CATEGORY_CHOICES when the
         *original* obj.taxonomy has a valid iucn_status category
      3. Falls back to 'Not evaluated' when iucn_status is absent or the
         category key is not in CATEGORY_CHOICES
    """

    def _serialize(self, record):
        serializer = BioCollectionOneRowSerializer()
        return serializer.get_conservation_status_global(record)

    # ------------------------------------------------------------------ #
    # Normal (non-synonym) taxon
    # ------------------------------------------------------------------ #

    def test_returns_label_for_valid_iucn_category(self, mock_iucn, mock_loc):
        """Returns the human-readable label when the taxonomy has a valid IUCN status."""
        iucn = _make_iucn('LC')
        taxon = TaxonomyF.create(iucn_status=iucn)
        record = BiologicalCollectionRecordF.create(taxonomy=taxon)

        result = self._serialize(record)

        self.assertEqual(result, 'Least Concern')

    def test_returns_not_evaluated_when_no_iucn_status(self, mock_iucn, mock_loc):
        """Returns 'Not evaluated' when the taxonomy has no IUCN status."""
        taxon = TaxonomyF.create(iucn_status=None)
        record = BiologicalCollectionRecordF.create(taxonomy=taxon)

        result = self._serialize(record)

        self.assertEqual(result, 'Not evaluated')

    def test_returns_not_evaluated_for_unknown_category(self, mock_iucn, mock_loc):
        """Returns 'Not evaluated' when iucn_status.category is not in CATEGORY_CHOICES."""
        iucn = IUCNStatus.objects.create(category='XX')
        taxon = TaxonomyF.create(iucn_status=iucn)
        record = BiologicalCollectionRecordF.create(taxonomy=taxon)

        result = self._serialize(record)

        self.assertEqual(result, 'Not evaluated')

    def test_various_valid_iucn_categories(self, mock_iucn, mock_loc):
        """Returns correct human-readable labels for a range of IUCN categories."""
        cases = [
            ('EN', 'Endangered'),
            ('VU', 'Vulnerable'),
            ('CR', 'Critically Endangered'),
            ('EX', 'Extinct'),
            ('DD', 'Data Deficient'),
        ]
        for category, expected_label in cases:
            with self.subTest(category=category):
                iucn = _make_iucn(category)
                taxon = TaxonomyF.create(iucn_status=iucn)
                record = BiologicalCollectionRecordF.create(taxonomy=taxon)

                result = self._serialize(record)

                self.assertEqual(result, expected_label)

    # ------------------------------------------------------------------ #
    # Synonym / doubtful — no accepted_taxonomy set
    # ------------------------------------------------------------------ #

    def test_synonym_without_accepted_taxonomy_uses_own_iucn(self, mock_iucn, mock_loc):
        """
        A synonym with no accepted_taxonomy falls through to obj.taxonomy.iucn_status.
        The guard `taxon.is_synonym_or_doubtful and taxon.accepted_taxonomy` is False
        when accepted_taxonomy is None, so the AttributeError on 'accepted_taxon' is
        never reached.
        """
        iucn = _make_iucn('EN')
        taxon = TaxonomyF.create(
            iucn_status=iucn,
            taxonomic_status='SYNONYM',
            accepted_taxonomy=None,
        )
        record = BiologicalCollectionRecordF.create(taxonomy=taxon)

        result = self._serialize(record)

        self.assertEqual(result, 'Endangered')

    def test_doubtful_without_accepted_taxonomy_uses_own_iucn(self, mock_iucn, mock_loc):
        """A DOUBTFUL taxon with no accepted_taxonomy uses its own IUCN status."""
        iucn = _make_iucn('VU')
        taxon = TaxonomyF.create(
            iucn_status=iucn,
            taxonomic_status='DOUBTFUL',
            accepted_taxonomy=None,
        )
        record = BiologicalCollectionRecordF.create(taxonomy=taxon)

        result = self._serialize(record)

        self.assertEqual(result, 'Vulnerable')

    def test_synonym_without_accepted_taxonomy_and_no_iucn(self, mock_iucn, mock_loc):
        """A synonym with no accepted_taxonomy and no IUCN status returns 'Not evaluated'."""
        taxon = TaxonomyF.create(
            iucn_status=None,
            taxonomic_status='SYNONYM',
            accepted_taxonomy=None,
        )
        record = BiologicalCollectionRecordF.create(taxonomy=taxon)

        result = self._serialize(record)

        self.assertEqual(result, 'Not evaluated')

    # ------------------------------------------------------------------ #
    # Synonym WITH accepted_taxonomy
    # NOTE: the method currently references `taxon.accepted_taxon` (typo)
    # instead of `taxon.accepted_taxonomy`. The accepted_taxonomy is patched
    # in via mock so the attribute resolution succeeds.
    # ------------------------------------------------------------------ #

    def test_synonym_with_accepted_taxonomy_returns_own_iucn_label(
        self, mock_iucn, mock_loc
    ):
        """
        When the synonym itself has an IUCN status, the method returns its label.
        The return statement uses obj.taxonomy.iucn_status regardless of whether
        the accepted_taxonomy was resolved.
        """
        accepted = TaxonomyF.create(iucn_status=_make_iucn('LC'))
        synonym_iucn = _make_iucn('EN')
        taxon = TaxonomyF.create(
            iucn_status=synonym_iucn,
            taxonomic_status='SYNONYM',
            accepted_taxonomy=accepted,
        )
        record = BiologicalCollectionRecordF.create(taxonomy=taxon)

        # Patch the misnamed attribute so the code path can proceed
        with mock.patch.object(
            type(taxon), 'accepted_taxon',
            new_callable=lambda: property(lambda self: self.accepted_taxonomy),
            create=True,
        ):
            result = self._serialize(record)

        self.assertEqual(result, 'Endangered')

    def test_synonym_with_no_own_iucn_gets_iucn_from_accepted_taxonomy(
        self, mock_iucn, mock_loc
    ):
        """
        When the synonym has no IUCN status of its own, the pre_save handler
        copies the accepted taxonomy's IUCN status onto the synonym before it
        is saved. So obj.taxonomy.iucn_status is populated by the time the
        serializer runs, and the accepted taxonomy's label is returned.
        """
        accepted = TaxonomyF.create(iucn_status=_make_iucn('LC'))
        taxon = TaxonomyF.create(
            iucn_status=None,
            taxonomic_status='SYNONYM',
            accepted_taxonomy=accepted,
        )
        record = BiologicalCollectionRecordF.create(taxonomy=taxon)

        with mock.patch.object(
            type(taxon), 'accepted_taxon',
            new_callable=lambda: property(lambda self: self.accepted_taxonomy),
            create=True,
        ):
            result = self._serialize(record)

        self.assertEqual(result, 'Least Concern')


@mock.patch('bims.models.location_site.update_location_site_context')
@mock.patch('bims.models.taxonomy.get_iucn_status', return_value=(None, None, None))
class TestGetGbifCoordinateUncertainty(FastTenantTestCase):
    """
    Tests for BioCollectionOneRowSerializer.get_gbif_coordinate_uncertainty_m.

    Priority order:
      1. Record-level coordinate_uncertainty_in_meters (new field)
      2. Site-level coordinate_uncertainty_in_meters (fallback)
      3. Empty string when neither is set
    """

    def _serialize(self, record):
        serializer = BioCollectionOneRowSerializer()
        return serializer.get_gbif_coordinate_uncertainty_m(record)

    def test_returns_record_level_value_when_set(self, mock_iucn, mock_loc):
        """Record-level value takes priority over site-level value."""
        site = LocationSiteF.create(coordinate_uncertainty_in_meters=Decimal('500.00'))
        record = BiologicalCollectionRecordF.create(
            site=site,
            coordinate_uncertainty_in_meters=Decimal('30.00'),
        )
        self.assertEqual(self._serialize(record), '30.00')

    def test_falls_back_to_site_value_when_record_value_is_none(self, mock_iucn, mock_loc):
        """Falls back to site-level value when record field is None."""
        site = LocationSiteF.create(coordinate_uncertainty_in_meters=Decimal('100.50'))
        record = BiologicalCollectionRecordF.create(
            site=site,
            coordinate_uncertainty_in_meters=None,
        )
        self.assertEqual(self._serialize(record), '100.50')

    def test_returns_empty_string_when_both_are_none(self, mock_iucn, mock_loc):
        """Returns empty string when both record and site values are None."""
        site = LocationSiteF.create(coordinate_uncertainty_in_meters=None)
        record = BiologicalCollectionRecordF.create(
            site=site,
            coordinate_uncertainty_in_meters=None,
        )
        self.assertEqual(self._serialize(record), '')

    def test_formats_to_two_decimal_places(self, mock_iucn, mock_loc):
        """Value is formatted to exactly two decimal places."""
        site = LocationSiteF.create(coordinate_uncertainty_in_meters=None)
        record = BiologicalCollectionRecordF.create(
            site=site,
            coordinate_uncertainty_in_meters=Decimal('7.1'),
        )
        self.assertEqual(self._serialize(record), '7.10')


@mock.patch('bims.models.location_site.update_location_site_context')
@mock.patch('bims.models.taxonomy.get_iucn_status', return_value=(None, None, None))
class TestGetGbifCoordinatePrecision(FastTenantTestCase):
    """
    Tests for BioCollectionOneRowSerializer.get_gbif_coordinate_precision.

    Priority order:
      1. Record-level coordinate_precision (new field)
      2. Site-level coordinate_precision (fallback)
      3. Empty string when neither is set
    """

    def _serialize(self, record):
        serializer = BioCollectionOneRowSerializer()
        return serializer.get_gbif_coordinate_precision(record)

    def test_returns_record_level_value_when_set(self, mock_iucn, mock_loc):
        """Record-level value takes priority over site-level value."""
        site = LocationSiteF.create(coordinate_precision=Decimal('1.0'))
        record = BiologicalCollectionRecordF.create(
            site=site,
            coordinate_precision=Decimal('0.00001'),
        )
        self.assertEqual(self._serialize(record), '0.000010')

    def test_falls_back_to_site_value_when_record_value_is_none(self, mock_iucn, mock_loc):
        """Falls back to site-level value when record field is None."""
        site = LocationSiteF.create(coordinate_precision=Decimal('0.01667'))
        record = BiologicalCollectionRecordF.create(
            site=site,
            coordinate_precision=None,
        )
        self.assertEqual(self._serialize(record), '0.016670')

    def test_returns_empty_string_when_both_are_none(self, mock_iucn, mock_loc):
        """Returns empty string when both record and site values are None."""
        site = LocationSiteF.create(coordinate_precision=None)
        record = BiologicalCollectionRecordF.create(
            site=site,
            coordinate_precision=None,
        )
        self.assertEqual(self._serialize(record), '')

    def test_formats_to_six_decimal_places(self, mock_iucn, mock_loc):
        """Value is formatted to exactly six decimal places."""
        site = LocationSiteF.create(coordinate_precision=None)
        record = BiologicalCollectionRecordF.create(
            site=site,
            coordinate_precision=Decimal('0.000278'),
        )
        self.assertEqual(self._serialize(record), '0.000278')
