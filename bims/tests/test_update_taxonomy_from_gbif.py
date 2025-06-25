# tests/test_update_taxonomy_from_gbif.py
from django.test import TestCase
from unittest.mock import patch, MagicMock

from bims.models import (
    TaxonomicRank,
    TaxonomicStatus, Taxonomy,
)
from bims.tests.model_factories import (
    TaxonomyF,
)
from bims.utils.gbif import update_taxonomy_from_gbif


class UpdateTaxonomyFromGbifTests(TestCase):
    """
    Exhaustively exercises `update_taxonomy_from_gbif`
    with realistic mocks for every logical branch.
    """

    def setUp(self):
        # A kingdom taxon that many tests will reuse
        self.kingdom = TaxonomyF.create(
            gbif_key=1,
            scientific_name="Animalia",
            canonical_name="Animalia",
            taxonomic_status=TaxonomicStatus.ACCEPTED.name,
            rank=TaxonomicRank.KINGDOM.name,
        )

        # Common vernacular response used by several tests
        self.vernacular_payload = {
            "results": [
                {
                    "vernacularName": "tiger",
                    "language": "en",
                    "source": "GBIF",
                    "taxonKey": 100,
                }
            ]
        }

    # ------------------------------------------------------------------ #
    # 1. Existing taxon with parent → early return
    # ------------------------------------------------------------------ #
    @patch("bims.utils.gbif.get_species")
    def test_early_return_when_taxon_has_parent(self, mock_get_species):
        genus = TaxonomyF.create(
            gbif_key=10,
            scientific_name="Panthera",
            canonical_name="Panthera",
            taxonomic_status=TaxonomicStatus.ACCEPTED.name,
            rank=TaxonomicRank.GENUS.name,
            parent=self.kingdom,
        )

        result = update_taxonomy_from_gbif(10)
        self.assertEqual(result.pk, genus.pk)
        mock_get_species.assert_not_called()

    # ------------------------------------------------------------------ #
    # 2. Existing kingdom taxon → early return (no parent required)
    # ------------------------------------------------------------------ #
    @patch("bims.utils.gbif.get_species")
    def test_early_return_when_rank_is_kingdom(self, mock_get_species):
        result = update_taxonomy_from_gbif(self.kingdom.gbif_key)
        self.assertEqual(result.pk, self.kingdom.pk)
        mock_get_species.assert_not_called()

    # ------------------------------------------------------------------ #
    # 3. Non-synonym creation (new species) with vernacular + parent fetch
    # ------------------------------------------------------------------ #
    @patch("bims.utils.gbif.get_vernacular_names")
    @patch("bims.utils.gbif.get_species")
    def test_create_species_with_parent_and_vernaculars(
        self, mock_get_species, mock_get_vernacular_names
    ):
        """
        Creates a new species (Panthera tigris) +
        its genus (Panthera) and adds vernacular names.
        """
        # ─── Mock remote payloads ───────────────────────────────────────
        mock_get_species.side_effect = lambda k: {
            50: {  # genus (parent)
                "key": 50,
                "scientificName": "Panthera",
                "canonicalName": "Panthera",
                "taxonomicStatus": "ACCEPTED",
                "rank": "GENUS",
                "authorship": "",
                "parentKey": 1,
            },
            100: {  # species
                "key": 100,
                "scientificName": "Panthera tigris",
                "canonicalName": "Panthera tigris",
                "taxonomicStatus": "ACCEPTED",
                "rank": "SPECIES",
                "authorship": "Linnaeus, 1758",
                "parentKey": 50,
            },
        }[k]

        mock_get_vernacular_names.return_value = self.vernacular_payload

        # ─── Call under test ────────────────────────────────────────────
        taxon = update_taxonomy_from_gbif(100)

        # ─── Assertions ────────────────────────────────────────────────
        self.assertEqual(taxon.canonical_name, "Panthera tigris")
        self.assertEqual(taxon.rank, TaxonomicRank.SPECIES.name)
        self.assertIsNotNone(taxon.parent)
        self.assertEqual(taxon.parent.canonical_name, "Panthera")
        self.assertEqual(taxon.vernacular_names.count(), 1)

    # ------------------------------------------------------------------ #
    # 4. Synonym where accepted taxon already exists in DB
    # ------------------------------------------------------------------ #
    @patch("bims.utils.gbif.get_vernacular_names", return_value={"results": []})
    @patch("bims.utils.gbif.get_species")
    def test_synonym_uses_existing_accepted_taxon(
        self, mock_get_species, _mock_get_vernacular_names
    ):
        accepted = TaxonomyF.create(
            gbif_key=300,
            scientific_name="Canis lupus",
            canonical_name="Canis lupus",
            taxonomic_status=TaxonomicStatus.ACCEPTED.name,
            rank=TaxonomicRank.SPECIES.name,
        )

        mock_get_species.return_value = {
            "key": 301,
            "scientificName": "Canis lycaon",
            "canonicalName": "Canis lycaon",
            "taxonomicStatus": "SYNONYM",
            "rank": "SPECIES",
            "authorship": "Say, 1823",
            "acceptedKey": 300,
            "parentKey": 1,
        }

        synonym = update_taxonomy_from_gbif(301)

        self.assertEqual(synonym.accepted_taxonomy_id, accepted.id)
        self.assertEqual(synonym.taxonomic_status, TaxonomicStatus.SYNONYM.name)

    # ------------------------------------------------------------------ #
    # 5. Synonym where accepted taxon NOT yet in DB (recursion branch)
    # ------------------------------------------------------------------ #
    @patch("bims.utils.gbif.get_vernacular_names", return_value={"results": []})
    @patch("bims.utils.gbif.get_species")
    def test_synonym_triggers_recursive_accepted_fetch(
        self, mock_get_species, _mock_get_vernacular_names
    ):
        """
        acceptedKey (400) is fetched recursively because
        it’s missing in DB when synonym 401 is processed.
        """
        def species_payload(k):
            if k == 400:  # accepted record
                return {
                    "key": 400,
                    "scientificName": "Puma concolor",
                    "canonicalName": "Puma concolor",
                    "taxonomicStatus": "ACCEPTED",
                    "rank": "SPECIES",
                    "authorship": "Linnaeus, 1771",
                    "parentKey": 1,
                }
            if k == 401:  # synonym to 400
                return {
                    "key": 401,
                    "scientificName": "Felis concolor",
                    "canonicalName": "Felis concolor",
                    "taxonomicStatus": "SYNONYM",
                    "rank": "SPECIES",
                    "authorship": "Linnaeus, 1771",
                    "acceptedKey": 400,
                    "parentKey": 1,
                }
            raise ValueError("unexpected key")

        mock_get_species.side_effect = species_payload

        synonym = update_taxonomy_from_gbif(401)

        # Accepted taxon was created via recursion
        accepted = Taxonomy.objects.get(gbif_key=400)

        self.assertEqual(synonym.accepted_taxonomy_id, accepted.id)
        self.assertEqual(accepted.taxonomic_status, TaxonomicStatus.ACCEPTED.name)
        # ensure recursion only called once per key
        self.assertEqual(mock_get_species.call_count, 2)
