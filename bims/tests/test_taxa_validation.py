from django_tenants.test.cases import FastTenantTestCase

from bims.scripts.species_keys import (
    TAXON, TAXON_RANK, TAXONOMIC_STATUS, AUTHORS, ACCEPTED_TAXON
)
from bims.scripts.taxa_validation import TaxaValidator
from bims.tests.model_factories import UploadSessionF


class TestTaxaValidatorHomonymy(FastTenantTestCase):
    """Tests for TaxaValidator's homonymy-vs-accepted/synonym detection."""

    def setUp(self):
        self.upload_session = UploadSessionF.create()
        self.validator = TaxaValidator(self.upload_session)

    def _make_row(self, name, rank, status, author, accepted_taxon=''):
        return {
            TAXON: name,
            TAXON_RANK: rank,
            TAXONOMIC_STATUS: status,
            AUTHORS: author,
            ACCEPTED_TAXON: accepted_taxon,
        }

    def test_accepted_and_synonym_same_name_no_warning(self):
        """An accepted taxon and its synonym sharing a name/rank but
        different authors should not trigger the homonymy warning."""
        rows = [
            self._make_row(
                'Gordius lineatus', 'Species', 'Accepted', 'Leidy, 1851'),
            self._make_row(
                'Gordius lineatus', 'Species', 'Synonym', 'Villot, 1886',
                accepted_taxon='Gordius lineatus'),
        ]

        self.validator._first_pass_collect_keys(rows)

        messages_row1 = self.validator._validate_row(rows[0], row_number=2)
        messages_row2 = self.validator._validate_row(rows[1], row_number=3)

        self.assertFalse(
            any('Homonymy' in m for m in messages_row1 + messages_row2)
        )

    def test_two_accepted_same_name_different_author_warns(self):
        """Two accepted rows sharing a name/rank with different authors
        is a genuine ambiguity and should still warn."""
        rows = [
            self._make_row(
                'Gordius lineatus', 'Species', 'Accepted', 'Leidy, 1851'),
            self._make_row(
                'Gordius lineatus', 'Species', 'Accepted', 'Villot, 1886'),
        ]

        self.validator._first_pass_collect_keys(rows)

        messages_row1 = self.validator._validate_row(rows[0], row_number=2)
        messages_row2 = self.validator._validate_row(rows[1], row_number=3)

        self.assertTrue(
            any('Homonymy' in m for m in messages_row1)
        )
        self.assertTrue(
            any('Homonymy' in m for m in messages_row2)
        )

    def test_two_synonyms_no_accepted_same_name_warns(self):
        """Two synonym rows sharing a name/rank with no accepted taxon
        among them is ambiguous and should still warn."""
        rows = [
            self._make_row(
                'Gordius lineatus', 'Species', 'Synonym', 'Leidy, 1851',
                accepted_taxon='Some Other Name'),
            self._make_row(
                'Gordius lineatus', 'Species', 'Synonym', 'Villot, 1886',
                accepted_taxon='Some Other Name'),
        ]

        self.validator._first_pass_collect_keys(rows)

        messages_row1 = self.validator._validate_row(rows[0], row_number=2)

        self.assertTrue(
            any('Homonymy' in m for m in messages_row1)
        )

    def test_accepted_with_two_synonyms_no_warning(self):
        """One accepted taxon with multiple synonyms of it sharing the
        same name/rank should not warn either."""
        rows = [
            self._make_row(
                'Gordius lineatus', 'Species', 'Accepted', 'Leidy, 1851'),
            self._make_row(
                'Gordius lineatus', 'Species', 'Synonym', 'Villot, 1886',
                accepted_taxon='Gordius lineatus'),
            self._make_row(
                'Gordius lineatus', 'Species', 'Synonym', 'Smith, 1900',
                accepted_taxon='Gordius lineatus'),
        ]

        self.validator._first_pass_collect_keys(rows)

        messages = []
        for i, row in enumerate(rows):
            messages.extend(self.validator._validate_row(row, row_number=i + 2))

        self.assertFalse(any('Homonymy' in m for m in messages))

    def test_same_name_rank_author_still_flagged_as_duplicate(self):
        """Exact duplicates (same name, rank, and author) must still be
        flagged as an ERROR, not silently suppressed."""
        rows = [
            self._make_row(
                'Gordius lineatus', 'Species', 'Accepted', 'Leidy, 1851'),
            self._make_row(
                'Gordius lineatus', 'Species', 'Accepted', 'Leidy, 1851'),
        ]

        self.validator._first_pass_collect_keys(rows)

        messages_row1 = self.validator._validate_row(rows[0], row_number=2)

        self.assertTrue(
            any('Duplicate taxon name' in m for m in messages_row1)
        )
