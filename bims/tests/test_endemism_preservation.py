"""
Tests to verify that endemism and origin are never silently cleared during:
  1. Occurrence CSV uploads (OccurrenceProcessor.taxonomy())
  2. TaxonomyUpdateProposal.approve()
"""
from django_tenants.test.cases import FastTenantTestCase

from bims.models.endemism import Endemism
from bims.models.taxonomy import Taxonomy
from bims.models.taxonomy_update_proposal import TaxonomyUpdateProposal
from bims.models.taxon_origin import TaxonOrigin
from bims.scripts.occurrences_upload import OccurrenceProcessor
from bims.tests.model_factories import (
    EndemismF,
    TaxonomyF,
    TaxonGroupF,
    UserF,
    TaxonomyUpdateProposalF,
)


class TestEndemismPreservationOnOccurrenceUpload(FastTenantTestCase):
    """
    OccurrenceProcessor.taxonomy() must NOT overwrite an existing endemism
    with None when the uploaded CSV row has no (or empty) Endemism column.
    """

    def setUp(self):
        self.endemism = EndemismF.create(name='Endemic')
        self.taxon_group = TaxonGroupF.create()
        self.taxonomy = TaxonomyF.create(
            canonical_name='Foo bar',
            rank='SPECIES',
            taxonomic_status='ACCEPTED',
            endemism=self.endemism,
        )
        self.taxonomy.taxongroup_set.add(self.taxon_group)

        self.processor = OccurrenceProcessor()
        self.processor.module_group = self.taxon_group

    def _make_record(self, endemism_value=None):
        record = {
            'Taxon': 'Foo bar',
            'Taxon rank': 'SPECIES',
        }
        if endemism_value is not None:
            record['Endemism'] = endemism_value
        return record

    def test_endemism_preserved_when_column_absent(self):
        """No Endemism column in CSV → existing endemism must not be cleared."""
        record = self._make_record()  # no 'Endemism' key
        result = self.processor.taxonomy(record)

        self.assertIsNotNone(result)
        result.refresh_from_db()
        self.assertEqual(result.endemism, self.endemism)

    def test_endemism_preserved_when_column_empty(self):
        """Empty Endemism column in CSV → existing endemism must not be cleared."""
        record = self._make_record(endemism_value='')
        result = self.processor.taxonomy(record)

        self.assertIsNotNone(result)
        result.refresh_from_db()
        self.assertEqual(result.endemism, self.endemism)

    def test_endemism_updated_when_column_provided(self):
        """Non-empty Endemism column → endemism should be updated."""
        record = self._make_record(endemism_value='Alien')
        result = self.processor.taxonomy(record)

        self.assertIsNotNone(result)
        result.refresh_from_db()
        self.assertIsNotNone(result.endemism)
        self.assertEqual(result.endemism.name, 'Alien')

    def test_endemism_set_when_taxon_had_none(self):
        """Taxon without endemism + CSV has a value → endemism should be assigned."""
        self.taxonomy.endemism = None
        self.taxonomy.save()

        record = self._make_record(endemism_value='Widespread')
        result = self.processor.taxonomy(record)

        self.assertIsNotNone(result)
        result.refresh_from_db()
        self.assertIsNotNone(result.endemism)
        self.assertEqual(result.endemism.name, 'Widespread')


class TestOriginPreservationOnOccurrenceUpload(FastTenantTestCase):
    """
    OccurrenceProcessor.taxonomy() must NOT overwrite an existing taxonomy.origin
    when the uploaded CSV row has no (or empty) Origin column.
    """

    def setUp(self):
        self.taxon_group = TaxonGroupF.create()
        self.origin = TaxonOrigin.objects.create(
            category='Indigenous',
            origin_key='indigenous',
        )
        self.taxonomy = TaxonomyF.create(
            canonical_name='Bar baz',
            rank='SPECIES',
            taxonomic_status='ACCEPTED',
            origin=self.origin,
        )
        self.taxonomy.taxongroup_set.add(self.taxon_group)

        self.processor = OccurrenceProcessor()
        self.processor.module_group = self.taxon_group

    def _make_record(self, origin_value=None):
        record = {
            'Taxon': 'Bar baz',
            'Taxon rank': 'SPECIES',
        }
        if origin_value is not None:
            record['Origin'] = origin_value
        return record

    def test_origin_preserved_when_column_absent(self):
        """No Origin column in CSV → existing origin must not be cleared."""
        record = self._make_record()
        result = self.processor.taxonomy(record)

        self.assertIsNotNone(result)
        result.refresh_from_db()
        self.assertEqual(result.origin, self.origin)

    def test_origin_preserved_when_column_empty(self):
        """Empty Origin column in CSV → existing origin must not be cleared."""
        record = self._make_record(origin_value='')
        result = self.processor.taxonomy(record)

        self.assertIsNotNone(result)
        result.refresh_from_db()
        self.assertEqual(result.origin, self.origin)

    def test_origin_preserved_when_value_unrecognised(self):
        """Unrecognised Origin value → existing origin must not be cleared."""
        record = self._make_record(origin_value='some-unknown-value')
        result = self.processor.taxonomy(record)

        self.assertIsNotNone(result)
        result.refresh_from_db()
        self.assertEqual(result.origin, self.origin)

    def test_origin_updated_when_column_provided(self):
        """Valid Origin column value → origin should be updated."""
        # Use get_or_create so the test works whether or not a TaxonOrigin
        # with origin_key='alien' already exists in the shared test DB.
        TaxonOrigin.objects.get_or_create(
            origin_key='alien',
            defaults={'category': 'Alien'},
        )
        record = self._make_record(origin_value='Non-native')
        result = self.processor.taxonomy(record)

        self.assertIsNotNone(result)
        result.refresh_from_db()
        self.assertIsNotNone(result.origin)
        self.assertEqual(result.origin.origin_key, 'alien')


class TestEndemismPreservationOnProposalApprove(FastTenantTestCase):
    """
    TaxonomyUpdateProposal.approve() must NOT copy a None endemism from the
    proposal onto the original taxonomy, overwriting an existing value.
    """

    def setUp(self):
        self.endemism = EndemismF.create(name='Endemic')
        self.reviewer = UserF.create(is_superuser=True)

        # Top-level taxon group (no parent) so get_top_level_parent() returns self
        self.taxon_group = TaxonGroupF.create()

        self.taxonomy = TaxonomyF.create(
            endemism=self.endemism,
            scientific_name='Foo bar sp.',
            canonical_name='Foo bar',
        )

        self.proposal = TaxonomyUpdateProposalF.create(
            original_taxonomy=self.taxonomy,
            taxon_group=self.taxon_group,
            taxon_group_under_review=self.taxon_group,
            endemism=None,  # proposal was created without endemism
            scientific_name=self.taxonomy.scientific_name,
            canonical_name=self.taxonomy.canonical_name,
            status='pending',
        )

    def test_approve_preserves_existing_endemism(self):
        """Approving a proposal with endemism=None must not clear the original endemism."""
        self.proposal.approve(self.reviewer, suppress_emails=True)

        self.taxonomy.refresh_from_db()
        self.assertEqual(
            self.taxonomy.endemism,
            self.endemism,
            'endemism was cleared by approve() even though the proposal had None'
        )

    def test_approve_sets_endemism_when_proposal_has_value(self):
        """Approving a proposal that has a specific endemism must update the original."""
        new_endemism = EndemismF.create(name='Widespread')
        self.proposal.endemism = new_endemism
        self.proposal.save()

        self.proposal.approve(self.reviewer, suppress_emails=True)

        self.taxonomy.refresh_from_db()
        self.assertEqual(
            self.taxonomy.endemism,
            new_endemism,
            'endemism from proposal was not applied to original taxonomy'
        )
