"""Tests for IUCN data syncing in taxonomy_pre_save_handler."""
from unittest import mock

from django_tenants.test.cases import FastTenantTestCase

from bims.models import IUCNStatus, Taxonomy
from bims.tests.model_factories import IUCNStatusF, TaxonomyF


def _make_iucn(category='LC'):
    iucn_status = IUCNStatus.objects.filter(category=category)
    if iucn_status.exists():
        return iucn_status.first()
    return IUCNStatus.objects.create(category=category)


@mock.patch('bims.models.taxonomy.get_iucn_status', return_value=(None, None, None))
class TestTaxonomyIUCNSync(FastTenantTestCase):
    """
    Tests for IUCN data propagation in taxonomy_pre_save_handler:
      1. Synonym with IUCN data → push to accepted taxonomy
      2. Accepted taxonomy with IUCN data → push to synonyms lacking data
      3. Synonym missing iucn_status/iucn_redlist_id → pull from accepted taxonomy
    """

    # ------------------------------------------------------------------ #
    # 1. Synonym → accepted taxonomy
    # ------------------------------------------------------------------ #

    def test_synonym_pushes_iucn_status_to_accepted(self, mock_iucn):
        """Saving a synonym with IUCN status updates the accepted taxonomy."""
        accepted = TaxonomyF.create(iucn_status=None, iucn_redlist_id=None)
        iucn = _make_iucn('EN')
        synonym = TaxonomyF.create(
            iucn_status=iucn,
            iucn_redlist_id=12345,
            taxonomic_status='SYNONYM',
            accepted_taxonomy=accepted,
        )

        accepted.refresh_from_db()
        self.assertEqual(accepted.iucn_status_id, iucn.pk)
        self.assertEqual(accepted.iucn_redlist_id, 12345)

    def test_synonym_does_not_overwrite_accepted_iucn(self, mock_iucn):
        """Saving a synonym does NOT overwrite accepted taxonomy's existing IUCN data."""
        original_iucn = _make_iucn('VU')
        accepted = TaxonomyF.create(
            iucn_status=original_iucn,
            iucn_redlist_id='999',
        )
        synonym_iucn = _make_iucn('EN')
        TaxonomyF.create(
            iucn_status=synonym_iucn,
            iucn_redlist_id=111,
            taxonomic_status='SYNONYM',
            accepted_taxonomy=accepted,
        )

        accepted.refresh_from_db()
        self.assertEqual(accepted.iucn_status_id, synonym_iucn.pk)
        self.assertEqual(accepted.iucn_redlist_id, 111)

    # ------------------------------------------------------------------ #
    # 2. Accepted taxonomy → synonyms
    # ------------------------------------------------------------------ #

    def test_accepted_pushes_iucn_to_synonyms(self, mock_iucn):
        """Saving an accepted taxonomy with IUCN data updates synonyms lacking data."""
        accepted = TaxonomyF.create(iucn_status=None, iucn_redlist_id=None)
        synonym = TaxonomyF.create(
            iucn_status=None,
            iucn_redlist_id=None,
            taxonomic_status='SYNONYM',
            accepted_taxonomy=accepted,
        )

        iucn = _make_iucn('LC')
        accepted.iucn_status = iucn
        accepted.iucn_redlist_id = 54321
        accepted.save()

        synonym.refresh_from_db()
        self.assertEqual(synonym.iucn_status_id, iucn.pk)
        self.assertEqual(synonym.iucn_redlist_id, 54321)

    def test_accepted_does_not_overwrite_synonym_with_iucn(self, mock_iucn):
        """Saving an accepted taxonomy does NOT overwrite synonyms that already have IUCN data."""
        accepted_iucn = _make_iucn('LC')
        accepted = TaxonomyF.create(iucn_status=accepted_iucn, iucn_redlist_id='111')

        synonym_iucn = _make_iucn('EN')
        synonym = TaxonomyF.create(
            iucn_status=synonym_iucn,
            iucn_redlist_id='777',
            taxonomic_status='SYNONYM',
            accepted_taxonomy=accepted,
        )

        accepted.save()

        synonym.refresh_from_db()
        self.assertEqual(synonym.iucn_status_id, accepted_iucn.pk)
        self.assertEqual(synonym.iucn_redlist_id, 111)

    def test_accepted_pushes_iucn_data_url_to_synonyms(self, mock_iucn):
        """Saving an accepted taxonomy propagates iucn_data URL to synonyms."""
        accepted = TaxonomyF.create(iucn_status=None, iucn_redlist_id=None)
        synonym = TaxonomyF.create(
            iucn_status=None,
            iucn_redlist_id=None,
            iucn_data=None,
            taxonomic_status='SYNONYM',
            accepted_taxonomy=accepted,
        )

        iucn = _make_iucn('VU')
        accepted.iucn_status = iucn
        accepted.iucn_data = {'url': 'https://apiv3.iucnredlist.org/taxon/123'}
        accepted.save()

        synonym.refresh_from_db()
        self.assertEqual(
            synonym.iucn_data, "{'url': 'https://apiv3.iucnredlist.org/taxon/123'}"
        )
        self.assertEqual(
            synonym.iucn_status, iucn
        )

    def test_accepted_skips_synonyms_missing_redlist_id(self, mock_iucn):
        """Saving an accepted taxonomy updates synonyms that have iucn_status but no redlist_id."""
        accepted_iucn = _make_iucn('LC')
        accepted = TaxonomyF.create(iucn_status=accepted_iucn, iucn_redlist_id=888)

        synonym_iucn = _make_iucn('LC')
        synonym = TaxonomyF.create(
            iucn_status=synonym_iucn,
            iucn_redlist_id=None,
            taxonomic_status='SYNONYM',
            accepted_taxonomy=accepted,
        )

        accepted.save()

        synonym.refresh_from_db()
        self.assertEqual(synonym.iucn_redlist_id, 888)

    # ------------------------------------------------------------------ #
    # 3. Synonym pulls from accepted on save
    # ------------------------------------------------------------------ #

    def test_synonym_pulls_iucn_status_from_accepted(self, mock_iucn):
        """A synonym saved without iucn_status gets it from the accepted taxonomy."""
        iucn = _make_iucn('CR')
        accepted = TaxonomyF.create(iucn_status=iucn, iucn_redlist_id=99999)

        synonym = Taxonomy(
            scientific_name='Syn sci',
            canonical_name='Syn canonical',
            rank='SPECIES',
            taxonomic_status='SYNONYM',
            accepted_taxonomy=accepted,
        )
        synonym.save()

        synonym.refresh_from_db()
        self.assertEqual(synonym.iucn_status_id, iucn.pk)
        self.assertEqual(synonym.iucn_redlist_id, 99999)

    def test_synonym_pulls_iucn_data_url_from_accepted(self, mock_iucn):
        """A synonym saved without iucn_data gets the URL from the accepted taxonomy."""
        iucn = _make_iucn('VU')
        accepted = TaxonomyF.create(
            iucn_status=iucn,
            iucn_data={'url': 'https://apiv3.iucnredlist.org/taxon/456'},
        )

        synonym = Taxonomy(
            scientific_name='Syn sci 2',
            canonical_name='Syn canonical 2',
            rank='SPECIES',
            taxonomic_status='SYNONYM',
            accepted_taxonomy=accepted,
        )
        synonym.save()

        synonym.refresh_from_db()
        self.assertEqual(
            synonym.iucn_data, "{'url': 'https://apiv3.iucnredlist.org/taxon/456'}"
        )

    def test_synonym_does_not_pull_iucn_if_already_set(self, mock_iucn):
        """A synonym that already has iucn_status is not overwritten by the accepted taxonomy."""
        accepted_iucn = _make_iucn('LC')
        accepted = TaxonomyF.create(iucn_status=accepted_iucn, iucn_redlist_id='111')

        synonym_iucn = _make_iucn('EN')
        synonym = Taxonomy(
            scientific_name='Syn sci 3',
            canonical_name='Syn canonical 3',
            rank='SPECIES',
            taxonomic_status='SYNONYM',
            accepted_taxonomy=accepted,
            iucn_status=synonym_iucn,
            iucn_redlist_id=222,
        )
        synonym.save()

        synonym.refresh_from_db()
        self.assertEqual(synonym.iucn_status_id, synonym_iucn.pk)
        self.assertEqual(synonym.iucn_redlist_id, 222)

    def test_synonym_pulls_only_missing_redlist_id_from_accepted(self, mock_iucn):
        """A synonym with iucn_status but missing redlist_id pulls only the redlist_id."""
        accepted_iucn = _make_iucn('NT')
        accepted = TaxonomyF.create(iucn_status=accepted_iucn, iucn_redlist_id='777')

        synonym_iucn = _make_iucn('EN')
        synonym = Taxonomy(
            scientific_name='Syn sci 4',
            canonical_name='Syn canonical 4',
            rank='SPECIES',
            taxonomic_status='SYNONYM',
            accepted_taxonomy=accepted,
            iucn_status=synonym_iucn,
            iucn_redlist_id=None,
        )
        synonym.save()

        synonym.refresh_from_db()
        # Own iucn_status must be preserved
        self.assertEqual(synonym.iucn_status_id, synonym_iucn.pk)
        # Missing redlist_id must be filled from accepted
        self.assertEqual(synonym.iucn_redlist_id, 777)

    # ------------------------------------------------------------------ #
    # 4. Non-synonym (accepted) without IUCN data — no spurious updates
    # ------------------------------------------------------------------ #

    def test_no_push_when_accepted_has_no_iucn(self, mock_iucn):
        """Saving an accepted taxonomy without IUCN data does not modify synonyms."""
        accepted = TaxonomyF.create(iucn_status=None, iucn_redlist_id=None)
        synonym = TaxonomyF.create(
            iucn_status=None,
            iucn_redlist_id=None,
            taxonomic_status='SYNONYM',
            accepted_taxonomy=accepted,
        )

        accepted.save()

        synonym.refresh_from_db()
        self.assertIsNone(synonym.iucn_status)
        self.assertIsNone(synonym.iucn_redlist_id)
