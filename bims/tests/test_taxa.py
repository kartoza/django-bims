from django.test import TestCase
from django_tenants.test.cases import FastTenantTestCase
from mock import patch

from bims.enums import TaxonomicGroupCategory, TaxonomicStatus
from bims.tasks import clear_taxa_not_associated_in_taxon_group
from bims.tests.model_factories import (
    TaxonomyF, BiologicalCollectionRecordF, TaxonGroupF, VernacularNameF, TaxonGroupTaxonomyF
)
from bims.utils.fetch_gbif import merge_taxa_data
from bims.models import Taxonomy, BiologicalCollectionRecord, TaxonGroup, IUCNStatus, TaxonExtraAttribute
from bims.models.taxonomy import TaxonTag
from bims.serializers.taxon_serializer import TaxonSerializer
from bims.views.download_csv_taxa_list import TaxaCSVSerializer
from bims.utils.taxonomy import canonical_with_subgenus
from bims.admin import TaxonomyAdminForm


class TestTaxaHelpers(TestCase):
    """Test all taxa helpers e.g. helper to merge to duplicated taxa"""

    def setUp(self):
        pass

    def test_merge_duplicated_taxa(self):
        """Test a function responsible for merging duplicated taxa"""

        vernacular_name_1 = VernacularNameF.create(
            name='common_name_1'
        )
        vernacular_name_2 = VernacularNameF.create(
            name='common_name_2'
        )
        vernacular_name_3 = VernacularNameF.create(
            name='common_name_3'
        )
        taxa_1 = TaxonomyF.create(
            canonical_name='taxa_to_merged',
            vernacular_names=(vernacular_name_1, )
        )
        taxa_2 = TaxonomyF.create(
            canonical_name='verified_taxa',
            vernacular_names=(vernacular_name_2, )
        )
        taxa_3 = TaxonomyF.create(
            canonical_name='taxa_to_merged',
            vernacular_names=(vernacular_name_3, vernacular_name_1)
        )
        collection = BiologicalCollectionRecordF.create(
            taxonomy=taxa_1
        )
        taxon_group = TaxonGroupF.create(
            name='test',
            taxonomies=(taxa_1, taxa_3)
        )
        taxon_group_2 = TaxonGroupF.create(
            name='test_3',
            taxonomies=(taxa_3, )
        )
        self.assertTrue(taxon_group.taxonomies.filter(id=taxa_1.id).exists())
        self.assertEqual(collection.taxonomy, taxa_1)

        # Merge all taxa
        merge_taxa_data(
            excluded_taxon=Taxonomy.objects.get(
                canonical_name='verified_taxa'),
            taxa_list=Taxonomy.objects.filter(canonical_name='taxa_to_merged')
        )
        # Collection should point to taxa_2
        self.assertEqual(BiologicalCollectionRecord.objects.get(
            id=collection.id
        ).taxonomy, taxa_2)

        # Taxon group should have updated taxa member
        self.assertFalse(
            TaxonGroup.objects.filter(
                id=taxon_group.id,
                taxonomies__id=taxa_1.id
            ).exists()
        )
        self.assertTrue(
            TaxonGroup.objects.filter(
                id=taxon_group.id,
                taxonomies__id=taxa_2.id
            ).exists()
        )
        self.assertTrue(
            TaxonGroup.objects.filter(
                id=taxon_group_2.id,
                taxonomies__id=taxa_2.id
            ).exists()
        )

        # Vernacular names should be updated
        self.assertEqual(
            Taxonomy.objects.get(id=taxa_2.id).vernacular_names.all().count(),
            3
        )

    def test_merge_duplicated_taxa_with_colliding_tag(self):
        """
        If the winner and a loser share a tag on a unique-together linked
        model (e.g. CustomTaggedTaxonomy on content_object+tag), reassigning
        the loser's row to the winner raises an IntegrityError. This must not
        poison the rest of the merge: later links (and taxa.delete()) should
        still run instead of raising TransactionManagementError.
        """
        tag = TaxonTag.objects.create(name='shared_tag')

        winner = TaxonomyF.create(canonical_name='verified_taxa')
        loser = TaxonomyF.create(canonical_name='taxa_to_merged')

        winner.biographic_distributions.add(tag)
        loser.biographic_distributions.add(tag)

        collection = BiologicalCollectionRecordF.create(taxonomy=loser)

        # Should not raise IntegrityError/TransactionManagementError.
        merge_taxa_data(
            excluded_taxon=winner,
            taxa_list=Taxonomy.objects.filter(id=loser.id)
        )

        # The loser is gone, and other links were still merged despite the
        # colliding tag being skipped.
        self.assertFalse(Taxonomy.objects.filter(id=loser.id).exists())
        self.assertEqual(
            BiologicalCollectionRecord.objects.get(id=collection.id).taxonomy,
            winner
        )
        self.assertEqual(
            list(winner.biographic_distributions.all()), [tag]
        )


class TaxaCSVSerializerTest(TestCase):
    def setUp(self):
        self.taxon_group = TaxonGroupF.create(
            category=TaxonomicGroupCategory.SPECIES_MODULE.name)

        self.vernacular_name = VernacularNameF(
            name='Human',
            language='en'
        )
        self.taxonomy = TaxonomyF.create(
            rank='SPECIES',
            canonical_name='Homo sapiens',
            scientific_name='Homo sapiens Linnaeus',
            endemism=None,
            iucn_status=IUCNStatus.objects.create(category='LC'),
            national_conservation_status=IUCNStatus.objects.create(category='NT'),
            col_id='XFF',
            additional_data={'Growth form': 'Tree'},
            vernacular_names=(self.vernacular_name,)
        )
        self.taxonomy.tags.add('freshwater', 'testing')
        self.taxonomy.biographic_distributions.add('ANT', 'TEST (?)')

        self.taxon_group.taxonomies.add(self.taxonomy)
        self.taxon_extra_attribute = TaxonExtraAttribute.objects.create(
            taxon_group=self.taxon_group,
            name='Growth form'
        )

    def test_serializer_fields(self):
        serializer = TaxaCSVSerializer(instance=self.taxonomy)
        serialized_data = serializer.data

        expected_fields = [
            'taxon_rank', 'kingdom', 'phylum', 'class_name', 'order', 'family', 'genus', 'species',
            'subspecies', 'taxon', 'common_name', 'origin',
            'endemism', 'conservation_status_global', 'conservation_status_national', 'on_gbif', 'gbif_link',
            'Growth form', 'freshwater', 'testing', 'ANT'
        ]

        for field in expected_fields:
            self.assertIn(field, serialized_data)

    def test_serializer_values(self):
        serializer = TaxaCSVSerializer(instance=self.taxonomy)
        serialized_data = serializer.data

        self.assertEqual(serialized_data['taxon_rank'], 'Species')
        self.assertEqual(serialized_data['species'], 'sapiens')
        self.assertEqual(serialized_data['taxon'], 'Homo sapiens')
        self.assertEqual(serialized_data['common_name'], 'Human')
        self.assertEqual(serialized_data['endemism'], 'Unknown')
        self.assertEqual(serialized_data['conservation_status_global'], 'Least Concern')
        self.assertEqual(serialized_data['conservation_status_national'], 'Near Threatened')
        self.assertEqual(serialized_data['on_gbif'], 'Yes')
        self.assertEqual(serialized_data['gbif_link'], 'https://www.gbif.org/taxon/XFF')
        self.assertEqual(serialized_data['Growth form'], 'Tree')
        self.assertEqual(serialized_data['freshwater'], 'Y')
        self.assertEqual(serialized_data['testing'], 'Y')
        self.assertEqual(serialized_data['ANT'], 'Y')
        self.assertEqual(serialized_data['TEST'], '?')
        self.assertTrue(len(serializer.context.get('tags')) > 0)

    def test_serializers_use_parent_genus_for_provisional_species_name(self):
        genus = Taxonomy.objects.create(
            canonical_name='Enteromius',
            scientific_name='Enteromius',
            rank='GENUS',
        )
        species = Taxonomy.objects.create(
            canonical_name='Enteromius sp. South Africa',
            scientific_name='Enteromius sp. South Africa',
            rank='SPECIES',
            parent=genus,
            hierarchical_data={
                'genus_name': 'Enteromius sp.',
                'species_name': 'sp. South Africa',
            },
        )

        taxon_data = TaxonSerializer(
            species,
            context={'validated': True}
        ).data
        csv_data = TaxaCSVSerializer(species).data

        self.assertEqual(taxon_data['genus'], 'Enteromius')
        self.assertEqual(csv_data['genus'], 'Enteromius')

    def test_taxon_with_subgenus_includes_parenthetical_in_download(self):
        """
        get_taxon should return "Genus (Subgenus) epithet" and
        get_scientific_name_and_authority should include it with the author.
        """
        genus = Taxonomy.objects.create(
            canonical_name='Thraulus', scientific_name='Thraulus', rank='GENUS',
        )
        subgenus = Taxonomy.objects.create(
            canonical_name='Thraulus (Masharikella)',
            scientific_name='Thraulus (Masharikella)',
            rank='SUBGENUS',
            parent=genus,
        )
        species = Taxonomy.objects.create(
            canonical_name='Thraulus (Masharikella) iteris',
            scientific_name='Thraulus (Masharikella) iteris Sartori & Salles, 2025',
            rank='SPECIES',
            parent=genus,
            subgenus=subgenus,
            author='Sartori & Salles, 2025',
        )

        serializer = TaxaCSVSerializer(instance=species)
        data = serializer.data

        self.assertEqual(data['taxon'], 'Thraulus (Masharikella) iteris')
        self.assertIn('Thraulus (Masharikella) iteris', data['scientific_name_and_authority'])

    def test_legacy_species_with_subgenus_fk_gets_parenthetical_in_download(self):
        """
        A species whose canonical_name lacks the subgenus parenthetical (legacy
        data uploaded before the fix) should still get the correct taxon name
        in the download output via the subgenus FK.
        """
        genus = Taxonomy.objects.create(
            canonical_name='Aedes', scientific_name='Aedes', rank='GENUS',
        )
        subgenus = Taxonomy.objects.create(
            canonical_name='Stegomyia',
            scientific_name='Stegomyia',
            rank='SUBGENUS',
            parent=genus,
        )
        species = Taxonomy.objects.create(
            canonical_name='Aedes aegypti',
            scientific_name='Aedes aegypti Linnaeus 1762',
            rank='SPECIES',
            parent=genus,
            subgenus=subgenus,
            author='Linnaeus 1762',
        )

        serializer = TaxaCSVSerializer(instance=species)
        data = serializer.data

        self.assertEqual(data['taxon'], 'Aedes (Stegomyia) aegypti')
        self.assertIn('Aedes (Stegomyia) aegypti', data['scientific_name_and_authority'])
        self.assertIn('Linnaeus 1762', data['scientific_name_and_authority'])


class TestGetTaxonRankNameThroughSynonymParent(TestCase):
    """
    Hierarchy resolution for a non-synonym taxon whose direct parent is a
    synonym with a detached parent (parent=None).

    This mimics the real-world case of a subspecies like
    "Gomphonema pumilum rigidum" whose parent species "Gomphonema pumilum"
    is a synonym and has had its parent removed by detach_synonym_parents.
    The fix in get_taxon_rank_name falls back to the synonym's
    accepted_taxonomy.parent chain to resolve ranks above the species.
    """

    def setUp(self):
        self.kingdom = Taxonomy.objects.create(
            canonical_name='Chromista', rank='KINGDOM'
        )
        self.phylum = Taxonomy.objects.create(
            canonical_name='Ochrophyta', rank='PHYLUM', parent=self.kingdom
        )
        self.klass = Taxonomy.objects.create(
            canonical_name='Bacillariophyceae', rank='CLASS', parent=self.phylum
        )
        self.order = Taxonomy.objects.create(
            canonical_name='Cymbellales', rank='ORDER', parent=self.klass
        )
        self.family = Taxonomy.objects.create(
            canonical_name='Gomphonemataceae', rank='FAMILY', parent=self.order
        )
        self.genus = Taxonomy.objects.create(
            canonical_name='Gomphonema', rank='GENUS', parent=self.family
        )
        # The accepted species - has a complete parent chain.
        self.accepted_species = Taxonomy.objects.create(
            canonical_name='Gomphonema pumilum',
            rank='SPECIES',
            parent=self.genus,
            taxonomic_status='ACCEPTED',
        )
        # The synonym species - same canonical name but marked as a synonym
        # and parent detached (as detach_synonym_parents does).
        self.synonym_species = Taxonomy.objects.create(
            canonical_name='Gomphonema pumilum',
            rank='SPECIES',
            parent=None,
            taxonomic_status='SYNONYM',
            accepted_taxonomy=self.accepted_species,
        )
        # The subspecies is NOT a synonym; its direct parent is the synonym.
        self.subspecies = Taxonomy.objects.create(
            canonical_name='Gomphonema pumilum rigidum',
            rank='SUBSPECIES',
            parent=self.synonym_species,
            taxonomic_status='ACCEPTED',
        )

    def test_genus_resolved_via_accepted_taxonomy_parent(self):
        self.assertEqual(self.subspecies.genus_name, 'Gomphonema')

    def test_family_resolved_via_accepted_taxonomy_parent(self):
        self.assertEqual(self.subspecies.family_name, 'Gomphonemataceae')

    def test_order_resolved_via_accepted_taxonomy_parent(self):
        self.assertEqual(self.subspecies.order_name, 'Cymbellales')

    def test_class_resolved_via_accepted_taxonomy_parent(self):
        self.assertEqual(self.subspecies.class_name, 'Bacillariophyceae')

    def test_phylum_resolved_via_accepted_taxonomy_parent(self):
        self.assertEqual(self.subspecies.phylum_name, 'Ochrophyta')

    def test_kingdom_resolved_via_accepted_taxonomy_parent(self):
        self.assertEqual(self.subspecies.kingdom_name, 'Chromista')

    def test_species_resolved_from_synonym_canonical(self):
        self.assertEqual(self.subspecies.species_name, 'pumilum')

    def test_csv_serializer_hierarchy_complete(self):
        serializer = TaxaCSVSerializer(instance=self.subspecies)
        data = serializer.data
        self.assertEqual(data['genus'], 'Gomphonema')
        self.assertEqual(data['family'], 'Gomphonemataceae')
        self.assertEqual(data['order'], 'Cymbellales')
        self.assertEqual(data['class_name'], 'Bacillariophyceae')
        self.assertEqual(data['phylum'], 'Ochrophyta')
        self.assertEqual(data['kingdom'], 'Chromista')
        self.assertEqual(data['species'], 'pumilum')
        self.assertEqual(data['subspecies'], 'rigidum')


class TestCanonicalWithSubgenus(TestCase):
    """Unit tests for the canonical_with_subgenus download utility."""

    def test_species_without_subgenus_unchanged(self):
        self.assertEqual(
            canonical_with_subgenus('Homo sapiens', 'Homo', ''),
            'Homo sapiens',
        )

    def test_species_already_has_parenthetical_unchanged(self):
        self.assertEqual(
            canonical_with_subgenus(
                'Aedes (Stegomyia) aegypti', 'Aedes', 'Stegomyia'),
            'Aedes (Stegomyia) aegypti',
        )

    def test_species_bare_subgenus_inserted(self):
        self.assertEqual(
            canonical_with_subgenus('Aedes aegypti', 'Aedes', 'Stegomyia'),
            'Aedes (Stegomyia) aegypti',
        )

    def test_subgenus_rank_bare_name_gets_genus_prefix(self):
        self.assertEqual(
            canonical_with_subgenus('Stegomyia', 'Aedes', 'Stegomyia'),
            'Aedes (Stegomyia)',
        )

    def test_subgenus_value_in_genus_parenthetical_form(self):
        """Subgenus stored as 'Aedes (Stegomyia)' — extract bare name correctly."""
        self.assertEqual(
            canonical_with_subgenus(
                'Aedes aegypti', 'Aedes', 'Aedes (Stegomyia)'),
            'Aedes (Stegomyia) aegypti',
        )

    def test_missing_genus_returns_canonical_unchanged(self):
        self.assertEqual(
            canonical_with_subgenus('Aedes aegypti', '', 'Stegomyia'),
            'Aedes aegypti',
        )

    def test_thraulus_masharikella_iteris(self):
        """Reproduce the exact example from the issue."""
        self.assertEqual(
            canonical_with_subgenus(
                'Thraulus iteris', 'Thraulus', 'Masharikella'),
            'Thraulus (Masharikella) iteris',
        )


class TestClearTaxaNotAssociatedInTaxonGroup(FastTenantTestCase):
    """
    Tests for bims.tasks.clear_taxa_not_associated_in_taxon_group
    """

    def setUp(self):
        # Common tree:
        self.root = TaxonomyF.create(rank="kingdom", canonical_name="Rootus")
        self.mid = TaxonomyF.create(rank="phylum", parent=self.root, canonical_name="Midus")
        self.leaf = TaxonomyF.create(rank="class", parent=self.mid, canonical_name="Leafus")

        self.orphan_kingdom = TaxonomyF.create(rank="kingdom", canonical_name="OrphanKingdom")

        self.orphan_referenced = TaxonomyF.create(rank="species", canonical_name="Orphanus ref")

        taxon_group = TaxonGroupF.create()
        TaxonGroupTaxonomyF.create(
            taxongroup=taxon_group,
            taxonomy=self.leaf,
        )

        if "accepted_taxonomy" in [f.name for f in Taxonomy._meta.get_fields()]:
            self.accepted = TaxonomyF.create(rank="species", canonical_name="Acceptedus")
            self.leaf.accepted_taxonomy = self.accepted
            self.leaf.save(update_fields=["accepted_taxonomy"])
        else:
            self.accepted = None

        self.bcr = BiologicalCollectionRecordF.create()
        setattr(self.bcr, "taxonomy_id", self.orphan_referenced.id)
        self.bcr.save(update_fields=["taxonomy"])
        self.mail_patcher = patch("bims.tasks.mail_superusers")
        self.mock_mail = self.mail_patcher.start()
        self.domain_patcher = patch("bims.tasks.get_domain_name", return_value="test.local")
        self.domain_patcher.start()

    def tearDown(self):
        self.mail_patcher.stop()
        self.domain_patcher.stop()

    def test_dry_run_keeps_group_ancestors_and_referenced_and_accepted(self):
        res = clear_taxa_not_associated_in_taxon_group(dry_run=True, keep_referenced_by_occurrences=True)

        self.assertTrue(res["ok"])
        self.assertTrue(res["dry_run"])
        self.assertEqual(res["domain"], "fast_test")

        self.assertEqual(res["kept_with_group"], 1)

        self.assertEqual(res["kept_ancestors_added"], 2)
        if self.accepted:
            self.assertIn("kept_referenced_by_occurrences", res)
        if self.bcr:
            self.assertEqual(res["kept_referenced_by_occurrences"], 1)

        # Dry run must not delete anything
        self.assertEqual(res["deleted"], 0)

        sample = res.get("sample_taxa_to_delete", [])
        sample_ids = {
            int(line.split(":", 1)[0])
            for line in sample
            if line.split(":", 1)[0].isdigit()
        }
        self.assertNotIn(self.leaf.id, sample_ids)
        self.assertNotIn(self.mid.id, sample_ids)
        self.assertNotIn(self.root.id, sample_ids)

    def test_real_run_deletes_unlinked_unreferenced_taxa(self):
        doomed = TaxonomyF.create(rank="species", canonical_name="Doomed")

        before = Taxonomy.objects.count()
        res = clear_taxa_not_associated_in_taxon_group(dry_run=False, keep_referenced_by_occurrences=True)

        after = Taxonomy.objects.count()

        self.assertTrue(res["ok"])
        self.assertFalse(Taxonomy.objects.filter(id=doomed.id).exists())
        self.assertGreater(res["deleted"], 0)
        self.assertLess(after, before)
        self.assertTrue(Taxonomy.objects.filter(id=self.root.id).exists())
        self.assertTrue(Taxonomy.objects.filter(id=self.mid.id).exists())
        self.assertTrue(Taxonomy.objects.filter(id=self.leaf.id).exists())
        if self.accepted:
            self.assertTrue(Taxonomy.objects.filter(id=self.accepted.id).exists())

    def test_real_run_respects_keep_referenced_by_occurrences_flag(self):
        """
        If keep_referenced_by_occurrences=False, the referenced orphan should be deleted (provided
        it isn't also kept for other reasons).
        """
        if not self.bcr:
            self.skipTest("Could not detect a Taxonomy FK on BCR; skipping referenced-by-occ test.")

        self.assertNotEqual(self.orphan_referenced.id, self.leaf.id)

        res = clear_taxa_not_associated_in_taxon_group(dry_run=False, keep_referenced_by_occurrences=False)
        self.assertTrue(res["ok"])

        self.assertFalse(Taxonomy.objects.filter(id=self.orphan_referenced.id).exists())

    def test_keeps_ancestors_when_only_leaf_is_grouped(self):
        """
        Ensure a leaf in a group keeps its ancestors up the chain on real run.
        """
        res = clear_taxa_not_associated_in_taxon_group(dry_run=False, keep_referenced_by_occurrences=True)
        self.assertTrue(res["ok"])

        self.assertTrue(Taxonomy.objects.filter(id=self.root.id).exists())
        self.assertTrue(Taxonomy.objects.filter(id=self.mid.id).exists())

    def test_breakdown_by_rank_is_present(self):
        """
        Ensure we return a rank breakdown list (when the field exists) and the shape is [{'rank': ..., 'n': ...}, ...]
        """
        res = clear_taxa_not_associated_in_taxon_group(dry_run=True, keep_referenced_by_occurrences=True)
        breakdown = res.get("delete_breakdown_by_rank", [])
        if breakdown:
            self.assertIsInstance(breakdown, list)
            self.assertIsInstance(breakdown[0], dict)
            self.assertIn("n", breakdown[0])
            self.assertIn("rank", breakdown[0])


class TaxonomyAdminFormDuplicateValidationTests(TestCase):
    """
    Tests for the duplicate-prevention rules implemented for issue #4844.
    """

    def test_manual_taxon_duplicate_canonical_name_is_rejected(self):
        """
        If a manual taxon (no gbif_key) with the same canonical_name already exists,
        the form should raise a validation error.
        """
        existing = TaxonomyF.create(
            canonical_name="Duplicata manualis",
            gbif_key=None,
        )

        form = TaxonomyAdminForm(
            data={
                "canonical_name": existing.canonical_name,
                "gbif_key": "",  # treated as no gbif_key
                # other required fields can be omitted; we only assert non-field error
            }
        )

        self.assertFalse(form.is_valid())
        errors = " ".join(form.non_field_errors())
        self.assertIn("A taxon with canonical name", errors)

    def test_gbif_synonym_with_existing_accepted_canonical_is_rejected(self):
        """
        If an ACCEPTED taxon with a canonical_name already exists,
        you cannot add another taxon with the same canonical_name
        and non-ACCEPTED status (synonym/doubtful/etc).
        """
        accepted = TaxonomyF.create(
            canonical_name="Canonica duplicata",
            gbif_key="111",
            taxonomic_status=TaxonomicStatus.ACCEPTED.name,
        )

        form = TaxonomyAdminForm(
            data={
                "canonical_name": accepted.canonical_name,
                "gbif_key": "222",
                "taxonomic_status": TaxonomicStatus.SYNONYM.name,
            }
        )

        self.assertFalse(form.is_valid())
        errors = " ".join(form.non_field_errors())
        self.assertIn("already exists in BIMS as an ACCEPTED taxon", errors)

    def test_gbif_accepted_with_different_author_is_rejected(self):
        """
        If an ACCEPTED taxon with a canonical_name and author already exists,
        you cannot add another ACCEPTED taxon with the same canonical_name
        but different author.
        """
        accepted = TaxonomyF.create(
            canonical_name="Authorensis duplicata",
            gbif_key="333",
            author="Smith, 1990",
            taxonomic_status=TaxonomicStatus.ACCEPTED.name,
        )

        form = TaxonomyAdminForm(
            data={
                "canonical_name": accepted.canonical_name,
                "gbif_key": "444",
                "author": "Jones, 2001",
                "taxonomic_status": TaxonomicStatus.ACCEPTED.name,
            }
        )

        self.assertFalse(form.is_valid())
        errors = " ".join(form.non_field_errors())
        self.assertIn("already an accepted taxon with this canonical name but a different author", errors)
