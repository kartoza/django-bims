# coding=utf-8
"""Tests for ModuleSummary organism-groups changes:
- Only top-level taxon groups (parent=None) appear in summary_data
- Children's accepted-species counts are rolled into the parent total
- FADA sites exclude taxa with no fada_id
- _validated_count_for_group deduplicates taxa shared across children
"""
from unittest.mock import patch

from django_tenants.test.cases import FastTenantTestCase

from bims.api_views.module_summary import ModuleSummary
from bims.enums.taxonomic_group_category import TaxonomicGroupCategory
from bims.enums.taxonomic_rank import TaxonomicRank
from bims.enums.taxonomic_status import TaxonomicStatus
from bims.tests.model_factories import TaxonomyF, TaxonGroupF, TaxonGroupTaxonomyF


def _accepted(**kwargs):
    """Create a Taxonomy with ACCEPTED status."""
    return TaxonomyF.create(
        taxonomic_status=TaxonomicStatus.ACCEPTED.name,
        rank=TaxonomicRank.SPECIES.name,
        **kwargs,
    )


def _species_group(name, parent=None, **kwargs):
    """Create a top-level or child SPECIES_MODULE TaxonGroup."""
    return TaxonGroupF.create(
        name=name,
        category=TaxonomicGroupCategory.SPECIES_MODULE.name,
        parent=parent,
        **kwargs,
    )


class TestModuleSummaryChildGroupsRollup(FastTenantTestCase):
    """Children are excluded from summary_data; their totals roll up to parent."""

    def setUp(self):
        self.ms = ModuleSummary()

        # Parent group with 1 accepted species of its own
        self.parent = _species_group('Fish')
        self.parent_taxon = _accepted(scientific_name='ParentFish')
        TaxonGroupTaxonomyF.create(taxongroup=self.parent, taxonomy=self.parent_taxon)

        # Child group with 1 unique accepted species
        self.child = _species_group('Child Fish', parent=self.parent)
        self.child_taxon = _accepted(scientific_name='ChildFish')
        TaxonGroupTaxonomyF.create(taxongroup=self.child, taxonomy=self.child_taxon)

    def test_summary_data_excludes_child_groups(self):
        data = self.ms.summary_data()
        self.assertIn('Fish', data)
        self.assertNotIn('Child Fish', data)

    def test_parent_total_validated_includes_child(self):
        data = self.ms.summary_data()
        # parent has 1 own + 1 child = 2
        self.assertEqual(data['Fish']['total_validated'], 2)

    def test_validated_count_for_group_deduplicates_shared_taxa(self):
        """A taxon linked to both parent and child is counted only once."""
        # Link child_taxon also directly to parent
        TaxonGroupTaxonomyF.create(
            taxongroup=self.parent, taxonomy=self.child_taxon
        )
        count = self.ms._validated_count_for_group(self.parent)
        # parent_taxon + child_taxon = 2 distinct, even though child_taxon
        # appears in both parent and child group
        self.assertEqual(count, 2)


class TestModuleSummaryTopLevelOnly(FastTenantTestCase):
    """Groups with no parent appear; groups with a parent do not."""

    def setUp(self):
        self.ms = ModuleSummary()
        self.top1 = _species_group('Algae')
        self.top2 = _species_group('Invertebrates')
        self.child = _species_group('Sub-invertebrates', parent=self.top2)

    def test_only_top_level_keys_present(self):
        data = self.ms.summary_data()
        self.assertIn('Algae', data)
        self.assertIn('Invertebrates', data)
        self.assertNotIn('Sub-invertebrates', data)

    def test_group_with_no_accepted_species_shows_zero(self):
        data = self.ms.summary_data()
        self.assertEqual(data['Algae']['total_validated'], 0)

    def test_general_summary_always_present(self):
        data = self.ms.summary_data()
        self.assertIn('general_summary', data)


class TestModuleSummaryNonFadaSite(FastTenantTestCase):
    """Non-FADA: all accepted taxa are counted regardless of fada_id."""

    def setUp(self):
        self.ms = ModuleSummary()
        self.group = _species_group('Birds')

        self.taxon_with_fada = _accepted(scientific_name='BirdA', fada_id='F001')
        self.taxon_no_fada = _accepted(scientific_name='BirdB', fada_id='')
        TaxonGroupTaxonomyF.create(taxongroup=self.group, taxonomy=self.taxon_with_fada)
        TaxonGroupTaxonomyF.create(taxongroup=self.group, taxonomy=self.taxon_no_fada)

    @patch('bims.api_views.module_summary.is_fada_site', return_value=False)
    def test_all_accepted_counted_on_non_fada(self, _mock):
        count = self.ms._validated_count_for_group(self.group)
        self.assertEqual(count, 2)

    @patch('bims.api_views.module_summary.is_fada_site', return_value=False)
    def test_summary_data_non_fada(self, _mock):
        data = self.ms.summary_data()
        self.assertEqual(data['Birds']['total_validated'], 2)


class TestModuleSummaryFadaSite(FastTenantTestCase):
    """FADA: only taxa with a non-empty fada_id are counted."""

    def setUp(self):
        self.ms = ModuleSummary()
        self.group = _species_group('Insects')

        self.taxon_with_fada = _accepted(scientific_name='InsectA', fada_id='F010')
        self.taxon_null_fada = _accepted(scientific_name='InsectB', fada_id=None)
        self.taxon_empty_fada = _accepted(scientific_name='InsectC', fada_id='')
        for t in (self.taxon_with_fada, self.taxon_null_fada, self.taxon_empty_fada):
            TaxonGroupTaxonomyF.create(taxongroup=self.group, taxonomy=t)

    @patch('bims.api_views.module_summary.is_fada_site', return_value=True)
    def test_only_fada_taxa_counted(self, _mock):
        count = self.ms._validated_count_for_group(self.group)
        self.assertEqual(count, 1)

    @patch('bims.api_views.module_summary.is_fada_site', return_value=True)
    def test_summary_data_fada(self, _mock):
        data = self.ms.summary_data()
        self.assertEqual(data['Insects']['total_validated'], 1)


class TestModuleSummaryFadaChildRollup(FastTenantTestCase):
    """FADA child rollup: only fada-tagged taxa from the whole subtree count."""

    def setUp(self):
        self.ms = ModuleSummary()
        self.parent = _species_group('Reptiles')

        # parent-level taxon: has fada_id
        self.p_taxon = _accepted(scientific_name='ParentReptile', fada_id='R001')
        TaxonGroupTaxonomyF.create(taxongroup=self.parent, taxonomy=self.p_taxon)

        # child group: one fada, one not
        self.child = _species_group('Sub-reptiles', parent=self.parent)
        self.c_fada = _accepted(scientific_name='ChildReptileA', fada_id='R002')
        self.c_no_fada = _accepted(scientific_name='ChildReptileB', fada_id='')
        TaxonGroupTaxonomyF.create(taxongroup=self.child, taxonomy=self.c_fada)
        TaxonGroupTaxonomyF.create(taxongroup=self.child, taxonomy=self.c_no_fada)

    @patch('bims.api_views.module_summary.is_fada_site', return_value=True)
    def test_child_not_in_summary(self, _mock):
        data = self.ms.summary_data()
        self.assertNotIn('Sub-reptiles', data)

    @patch('bims.api_views.module_summary.is_fada_site', return_value=True)
    def test_parent_total_counts_only_fada_across_subtree(self, _mock):
        data = self.ms.summary_data()
        # p_taxon (fada) + c_fada (fada) = 2; c_no_fada excluded
        self.assertEqual(data['Reptiles']['total_validated'], 2)

    @patch('bims.api_views.module_summary.is_fada_site', return_value=False)
    def test_parent_total_counts_all_across_subtree_non_fada(self, _mock):
        data = self.ms.summary_data()
        # p_taxon + c_fada + c_no_fada = 3
        self.assertEqual(data['Reptiles']['total_validated'], 3)


class TestModuleSummaryNonAcceptedExcluded(FastTenantTestCase):
    """Only ACCEPTED taxonomy status counts; synonyms/doubtful do not."""

    def setUp(self):
        self.ms = ModuleSummary()
        self.group = _species_group('Amphibians')

        self.accepted = _accepted(scientific_name='FrogA')
        self.synonym = TaxonomyF.create(
            scientific_name='FrogB',
            taxonomic_status=TaxonomicStatus.SYNONYM.name,
            rank=TaxonomicRank.SPECIES.name,
        )
        TaxonGroupTaxonomyF.create(taxongroup=self.group, taxonomy=self.accepted)
        TaxonGroupTaxonomyF.create(taxongroup=self.group, taxonomy=self.synonym)

    @patch('bims.api_views.module_summary.is_fada_site', return_value=False)
    def test_only_accepted_counted(self, _mock):
        count = self.ms._validated_count_for_group(self.group)
        self.assertEqual(count, 1)
