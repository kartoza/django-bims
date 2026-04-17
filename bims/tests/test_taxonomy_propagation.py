"""Tests for field propagation between accepted taxa and synonyms (taxonomy_pre_save_handler)."""
from unittest import mock

from django_tenants.test.cases import FastTenantTestCase

from bims.models import Taxonomy, IUCNStatus
from bims.models.endemism import Endemism
from bims.models.taxon_origin import TaxonOrigin
from bims.tests.model_factories import TaxonomyF, IUCNStatusF


def _make_origin(category='Native'):
    return TaxonOrigin.objects.create(category=category)


def _make_endemism(name='Endemic'):
    return Endemism.objects.create(name=name)


@mock.patch('bims.models.taxonomy.get_iucn_status', return_value=(None, None, None))
class TestTaxonomyOriginPropagation(FastTenantTestCase):
    """
    Tests for origin propagation in taxonomy_pre_save_handler.
    Propagation always overwrites — the latest save wins.

      1. Synonym with origin → push up to accepted (overwrites any existing value)
      2. Synonym without origin → pull down from accepted name
      3. Synonym with origin keeps its own value when saved (push path, not pull path)
      4. Accepted name with origin → push down to all synonyms (overwrites any existing value)
      5. No push when accepted name has no origin
    """

    def test_synonym_pushes_origin_to_accepted(self, mock_iucn):
        """Saving a synonym with an origin sets it on the accepted name."""
        accepted = TaxonomyF.create(origin=None)
        origin = _make_origin('Native')

        TaxonomyF.create(
            origin=origin,
            taxonomic_status='SYNONYM',
            accepted_taxonomy=accepted,
        )

        accepted.refresh_from_db()
        self.assertEqual(accepted.origin_id, origin.pk)

    def test_synonym_overwrites_accepted_origin(self, mock_iucn):
        """Saving a synonym with an origin overwrites the accepted name's existing origin."""
        original_origin = _make_origin('Native')
        accepted = TaxonomyF.create(origin=original_origin)

        synonym_origin = _make_origin('Alien')
        TaxonomyF.create(
            origin=synonym_origin,
            taxonomic_status='SYNONYM',
            accepted_taxonomy=accepted,
        )

        accepted.refresh_from_db()
        self.assertEqual(accepted.origin_id, synonym_origin.pk)

    def test_synonym_pulls_origin_from_accepted(self, mock_iucn):
        """A synonym saved without an origin inherits it from the accepted name."""
        origin = _make_origin('Native')
        accepted = TaxonomyF.create(origin=origin)

        synonym = Taxonomy(
            scientific_name='Syn sci',
            canonical_name='Syn canonical',
            rank='SPECIES',
            taxonomic_status='SYNONYM',
            accepted_taxonomy=accepted,
        )
        synonym.save()

        synonym.refresh_from_db()
        self.assertEqual(synonym.origin_id, origin.pk)

    def test_synonym_with_origin_keeps_own_value_on_save(self, mock_iucn):
        """A synonym that has its own origin keeps it when saved (push path taken, not pull)."""
        accepted_origin = _make_origin('Native')
        accepted = TaxonomyF.create(origin=accepted_origin)

        synonym_origin = _make_origin('Alien')
        synonym = Taxonomy(
            scientific_name='Syn sci 2',
            canonical_name='Syn canonical 2',
            rank='SPECIES',
            taxonomic_status='SYNONYM',
            accepted_taxonomy=accepted,
            origin=synonym_origin,
        )
        synonym.save()

        synonym.refresh_from_db()
        self.assertEqual(synonym.origin_id, synonym_origin.pk)

    def test_accepted_pushes_origin_to_synonyms(self, mock_iucn):
        """Saving an accepted name with an origin sets it on synonyms that lack one."""
        accepted = TaxonomyF.create(origin=None)
        synonym = TaxonomyF.create(
            origin=None,
            taxonomic_status='SYNONYM',
            accepted_taxonomy=accepted,
        )

        origin = _make_origin('Native')
        accepted.origin = origin
        accepted.save()

        synonym.refresh_from_db()
        self.assertEqual(synonym.origin_id, origin.pk)

    def test_accepted_overwrites_synonym_origin(self, mock_iucn):
        """Saving an accepted name with an origin overwrites synonyms' existing origin."""
        accepted_origin = _make_origin('Native')
        accepted = TaxonomyF.create(origin=accepted_origin)

        synonym_origin = _make_origin('Alien')
        synonym = TaxonomyF.create(
            origin=synonym_origin,
            taxonomic_status='SYNONYM',
            accepted_taxonomy=accepted,
        )

        accepted.save()

        synonym.refresh_from_db()
        self.assertEqual(synonym.origin_id, accepted_origin.pk)

    def test_no_push_when_accepted_has_no_origin(self, mock_iucn):
        """Saving an accepted name without an origin does not modify synonyms."""
        accepted = TaxonomyF.create(origin=None)
        synonym = TaxonomyF.create(
            origin=None,
            taxonomic_status='SYNONYM',
            accepted_taxonomy=accepted,
        )

        accepted.save()

        synonym.refresh_from_db()
        self.assertIsNone(synonym.origin)


@mock.patch('bims.models.taxonomy.get_iucn_status', return_value=(None, None, None))
class TestTaxonomyEndemismPropagation(FastTenantTestCase):
    """
    Tests for endemism propagation in taxonomy_pre_save_handler.
    Propagation always overwrites — the latest save wins.

      1. Synonym with endemism → push up to accepted (overwrites any existing value)
      2. Synonym without endemism → pull down from accepted name
      3. Synonym with endemism keeps its own value when saved (push path, not pull path)
      4. Accepted name with endemism → push down to all synonyms (overwrites any existing value)
      5. No push when accepted name has no endemism
    """

    def test_synonym_pushes_endemism_to_accepted(self, mock_iucn):
        """Saving a synonym with an endemism sets it on the accepted name."""
        accepted = TaxonomyF.create(endemism=None)
        endemism = _make_endemism('Endemic')

        TaxonomyF.create(
            endemism=endemism,
            taxonomic_status='SYNONYM',
            accepted_taxonomy=accepted,
        )

        accepted.refresh_from_db()
        self.assertEqual(accepted.endemism_id, endemism.pk)

    def test_synonym_not_overwrites_accepted_endemism(self, mock_iucn):
        """Saving a synonym with an endemism should not overwrite the accepted name's existing endemism."""
        original_endemism = _make_endemism('Endemic')
        accepted = TaxonomyF.create(endemism=original_endemism)

        synonym_endemism = _make_endemism('Near-endemic')
        TaxonomyF.create(
            endemism=synonym_endemism,
            taxonomic_status='SYNONYM',
            accepted_taxonomy=accepted,
        )

        accepted.refresh_from_db()
        self.assertNotEqual(accepted.endemism_id, synonym_endemism.pk)

    def test_synonym_pulls_endemism_from_accepted(self, mock_iucn):
        """A synonym saved without an endemism inherits it from the accepted name."""
        endemism = _make_endemism('Endemic')
        accepted = TaxonomyF.create(endemism=endemism)

        synonym = Taxonomy(
            scientific_name='Syn sci',
            canonical_name='Syn canonical',
            rank='SPECIES',
            taxonomic_status='SYNONYM',
            accepted_taxonomy=accepted,
        )
        synonym.save()

        synonym.refresh_from_db()
        self.assertEqual(synonym.endemism_id, endemism.pk)

    def test_synonym_with_endemism_keeps_own_value_on_save(self, mock_iucn):
        """A synonym that has its own endemism keeps it when saved (push path taken, not pull)."""
        accepted_endemism = _make_endemism('Endemic')
        accepted = TaxonomyF.create(endemism=accepted_endemism)

        synonym_endemism = _make_endemism('Near-endemic')
        synonym = Taxonomy(
            scientific_name='Syn sci 2',
            canonical_name='Syn canonical 2',
            rank='SPECIES',
            taxonomic_status='SYNONYM',
            accepted_taxonomy=accepted,
            endemism=synonym_endemism,
        )
        synonym.save()

        synonym.refresh_from_db()
        self.assertEqual(synonym.endemism_id, synonym_endemism.pk)

    def test_accepted_pushes_endemism_to_synonyms(self, mock_iucn):
        """Saving an accepted name with an endemism sets it on synonyms that lack one."""
        accepted = TaxonomyF.create(endemism=None)
        synonym = TaxonomyF.create(
            endemism=None,
            taxonomic_status='SYNONYM',
            accepted_taxonomy=accepted,
        )

        endemism = _make_endemism('Endemic')
        accepted.endemism = endemism
        accepted.save()

        synonym.refresh_from_db()
        self.assertEqual(synonym.endemism_id, endemism.pk)

    def test_accepted_overwrites_synonym_endemism(self, mock_iucn):
        """Saving an accepted name with an endemism overwrites synonyms' existing endemism."""
        accepted_endemism = _make_endemism('Endemic')
        accepted = TaxonomyF.create(endemism=accepted_endemism)

        synonym_endemism = _make_endemism('Near-endemic')
        synonym = TaxonomyF.create(
            endemism=synonym_endemism,
            taxonomic_status='SYNONYM',
            accepted_taxonomy=accepted,
        )

        accepted.save()

        synonym.refresh_from_db()
        self.assertEqual(synonym.endemism_id, accepted_endemism.pk)

    def test_no_push_when_accepted_has_no_endemism(self, mock_iucn):
        """Saving an accepted name without an endemism does not modify synonyms."""
        accepted = TaxonomyF.create(endemism=None)
        synonym = TaxonomyF.create(
            endemism=None,
            taxonomic_status='SYNONYM',
            accepted_taxonomy=accepted,
        )

        accepted.save()

        synonym.refresh_from_db()
        self.assertIsNone(synonym.endemism)


def _make_ncs(category='LC'):
    return IUCNStatusF.create(category=category)


@mock.patch('bims.models.taxonomy.get_iucn_status', return_value=(None, None, None))
class TestTaxonomyNationalConservationStatusPropagation(FastTenantTestCase):
    """
    Tests for national_conservation_status propagation in taxonomy_pre_save_handler.
    Propagation always overwrites — the latest save wins.

      1. Synonym with NCS → push up to accepted (overwrites any existing value)
      2. Synonym without NCS → pull down from accepted name
      3. Synonym with NCS keeps its own value when saved (push path, not pull path)
      4. Accepted name with NCS → push down to all synonyms (overwrites any existing value)
      5. No push when accepted name has no NCS
    """

    def test_synonym_pushes_ncs_to_accepted(self, mock_iucn):
        """Saving a synonym with a NCS sets it on the accepted name."""
        accepted = TaxonomyF.create(national_conservation_status=None)
        ncs = _make_ncs('LC')

        TaxonomyF.create(
            national_conservation_status=ncs,
            taxonomic_status='SYNONYM',
            accepted_taxonomy=accepted,
        )

        accepted.refresh_from_db()
        self.assertEqual(accepted.national_conservation_status_id, ncs.pk)

    def test_synonym_not_overwrites_accepted_ncs(self, mock_iucn):
        """Saving a synonym with a NCS should not overwrite the accepted name's existing NCS."""
        original_ncs = _make_ncs('LC')
        accepted = TaxonomyF.create(national_conservation_status=original_ncs)

        synonym_ncs = _make_ncs('EN')
        TaxonomyF.create(
            national_conservation_status=synonym_ncs,
            taxonomic_status='SYNONYM',
            accepted_taxonomy=accepted,
        )

        accepted.refresh_from_db()
        self.assertNotEqual(accepted.national_conservation_status_id, synonym_ncs.pk)

    def test_synonym_pulls_ncs_from_accepted(self, mock_iucn):
        """A synonym saved without a NCS inherits it from the accepted name."""
        ncs = _make_ncs('VU')
        accepted = TaxonomyF.create(national_conservation_status=ncs)

        synonym = Taxonomy(
            scientific_name='Syn sci',
            canonical_name='Syn canonical',
            rank='SPECIES',
            taxonomic_status='SYNONYM',
            accepted_taxonomy=accepted,
        )
        synonym.save()

        synonym.refresh_from_db()
        self.assertEqual(synonym.national_conservation_status_id, ncs.pk)

    def test_synonym_with_ncs_keeps_own_value_on_save(self, mock_iucn):
        """A synonym that has its own NCS keeps it when saved (push path taken, not pull)."""
        accepted_ncs = _make_ncs('LC')
        accepted = TaxonomyF.create(national_conservation_status=accepted_ncs)

        synonym_ncs = _make_ncs('CR')
        synonym = Taxonomy(
            scientific_name='Syn sci 2',
            canonical_name='Syn canonical 2',
            rank='SPECIES',
            taxonomic_status='SYNONYM',
            accepted_taxonomy=accepted,
            national_conservation_status=synonym_ncs,
        )
        synonym.save()

        synonym.refresh_from_db()
        self.assertEqual(synonym.national_conservation_status_id, synonym_ncs.pk)

    def test_accepted_pushes_ncs_to_synonyms(self, mock_iucn):
        """Saving an accepted name with a NCS sets it on synonyms that lack one."""
        accepted = TaxonomyF.create(national_conservation_status=None)
        synonym = TaxonomyF.create(
            national_conservation_status=None,
            taxonomic_status='SYNONYM',
            accepted_taxonomy=accepted,
        )

        ncs = _make_ncs('NT')
        accepted.national_conservation_status = ncs
        accepted.save()

        synonym.refresh_from_db()
        self.assertEqual(synonym.national_conservation_status_id, ncs.pk)

    def test_accepted_not_overwrites_synonym_ncs(self, mock_iucn):
        """Saving an accepted name with a NCS should not overwrite synonyms' existing NCS."""
        accepted_ncs = _make_ncs('LC')
        accepted = TaxonomyF.create(national_conservation_status=accepted_ncs)

        synonym_ncs = _make_ncs('EN')
        synonym = TaxonomyF.create(
            national_conservation_status=synonym_ncs,
            taxonomic_status='SYNONYM',
            accepted_taxonomy=accepted,
        )

        accepted.save()

        synonym.refresh_from_db()
        self.assertNotEqual(synonym.national_conservation_status_id, accepted_ncs.pk)

    def test_no_push_when_accepted_has_no_ncs(self, mock_iucn):
        """Saving an accepted name without a NCS does not modify synonyms."""
        accepted = TaxonomyF.create(national_conservation_status=None)
        synonym = TaxonomyF.create(
            national_conservation_status=None,
            taxonomic_status='SYNONYM',
            accepted_taxonomy=accepted,
        )

        accepted.save()

        synonym.refresh_from_db()
        self.assertIsNone(synonym.national_conservation_status)
