"""Tests for field propagation between accepted taxa and synonyms (taxonomy_pre_save_handler)."""
from unittest import mock

from django_tenants.test.cases import FastTenantTestCase

from bims.models import Taxonomy
from bims.models.endemism import Endemism
from bims.models.taxon_origin import TaxonOrigin
from bims.tests.model_factories import TaxonomyF


def _make_origin(category='Native'):
    return TaxonOrigin.objects.create(category=category)


def _make_endemism(name='Endemic'):
    return Endemism.objects.create(name=name)


@mock.patch('bims.models.taxonomy.get_iucn_status', return_value=(None, None, None))
class TestTaxonomyOriginPropagation(FastTenantTestCase):
    """
    Tests for origin propagation in taxonomy_pre_save_handler:
      1. Synonym with origin → push up to accepted name if it lacks one
      2. Synonym without origin → pull down from accepted name
      3. Synonym does not overwrite accepted name's existing origin
      4. Accepted name with origin → push down to synonyms that lack one
      5. Accepted name does not overwrite synonyms that already have an origin
      6. No push when accepted name has no origin
    """

    # ------------------------------------------------------------------ #
    # 1. Synonym → accepted name (push up)
    # ------------------------------------------------------------------ #

    def test_synonym_pushes_origin_to_accepted(self, mock_iucn):
        """Saving a synonym with an origin updates the accepted name if it lacks one."""
        accepted = TaxonomyF.create(origin=None)
        origin = _make_origin('Native')

        TaxonomyF.create(
            origin=origin,
            taxonomic_status='SYNONYM',
            accepted_taxonomy=accepted,
        )

        accepted.refresh_from_db()
        self.assertEqual(accepted.origin_id, origin.pk)

    def test_synonym_does_not_overwrite_accepted_origin(self, mock_iucn):
        """Saving a synonym does NOT overwrite the accepted name's existing origin."""
        original_origin = _make_origin('Native')
        accepted = TaxonomyF.create(origin=original_origin)

        synonym_origin = _make_origin('Alien')
        TaxonomyF.create(
            origin=synonym_origin,
            taxonomic_status='SYNONYM',
            accepted_taxonomy=accepted,
        )

        accepted.refresh_from_db()
        self.assertEqual(accepted.origin_id, original_origin.pk)

    # ------------------------------------------------------------------ #
    # 2. Synonym pulls from accepted on save
    # ------------------------------------------------------------------ #

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

    def test_synonym_does_not_pull_origin_if_already_set(self, mock_iucn):
        """A synonym that already has an origin is not overwritten by the accepted name."""
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

    # ------------------------------------------------------------------ #
    # 3. Accepted name → synonyms (push down)
    # ------------------------------------------------------------------ #

    def test_accepted_pushes_origin_to_synonyms(self, mock_iucn):
        """Saving an accepted name with an origin updates synonyms that lack one."""
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

    def test_accepted_does_not_overwrite_synonym_origin(self, mock_iucn):
        """Saving an accepted name does NOT overwrite synonyms that already have an origin."""
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
        self.assertEqual(synonym.origin_id, synonym_origin.pk)

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
    Tests for endemism propagation in taxonomy_pre_save_handler:
      1. Synonym with endemism → push up to accepted name if it lacks one
      2. Synonym without endemism → pull down from accepted name
      3. Synonym does not overwrite accepted name's existing endemism
      4. Accepted name with endemism → push down to synonyms that lack one
      5. Accepted name does not overwrite synonyms that already have an endemism
      6. No push when accepted name has no endemism
    """

    # ------------------------------------------------------------------ #
    # 1. Synonym → accepted name (push up)
    # ------------------------------------------------------------------ #

    def test_synonym_pushes_endemism_to_accepted(self, mock_iucn):
        """Saving a synonym with an endemism updates the accepted name if it lacks one."""
        accepted = TaxonomyF.create(endemism=None)
        endemism = _make_endemism('Endemic')

        TaxonomyF.create(
            endemism=endemism,
            taxonomic_status='SYNONYM',
            accepted_taxonomy=accepted,
        )

        accepted.refresh_from_db()
        self.assertEqual(accepted.endemism_id, endemism.pk)

    def test_synonym_does_not_overwrite_accepted_endemism(self, mock_iucn):
        """Saving a synonym does NOT overwrite the accepted name's existing endemism."""
        original_endemism = _make_endemism('Endemic')
        accepted = TaxonomyF.create(endemism=original_endemism)

        synonym_endemism = _make_endemism('Near-endemic')
        TaxonomyF.create(
            endemism=synonym_endemism,
            taxonomic_status='SYNONYM',
            accepted_taxonomy=accepted,
        )

        accepted.refresh_from_db()
        self.assertEqual(accepted.endemism_id, original_endemism.pk)

    # ------------------------------------------------------------------ #
    # 2. Synonym pulls from accepted on save
    # ------------------------------------------------------------------ #

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

    def test_synonym_does_not_pull_endemism_if_already_set(self, mock_iucn):
        """A synonym that already has an endemism is not overwritten by the accepted name."""
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

    # ------------------------------------------------------------------ #
    # 3. Accepted name → synonyms (push down)
    # ------------------------------------------------------------------ #

    def test_accepted_pushes_endemism_to_synonyms(self, mock_iucn):
        """Saving an accepted name with an endemism updates synonyms that lack one."""
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

    def test_accepted_does_not_overwrite_synonym_endemism(self, mock_iucn):
        """Saving an accepted name does NOT overwrite synonyms that already have an endemism."""
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
        self.assertEqual(synonym.endemism_id, synonym_endemism.pk)

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
