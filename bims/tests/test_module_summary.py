# coding=utf-8
"""Tests for ModuleSummary organism-groups changes:
- Only top-level taxon groups (parent=None) appear in summary_data
- Children's accepted-species counts are rolled into the parent total
- FADA sites exclude taxa with no fada_id
- _validated_count_for_group deduplicates taxa shared across children
- Conservation status chart counts occurrences by default, or distinct taxa
  when SiteSetting.conservation_status_chart_use_taxon_count is enabled
- the taxon count chart uses the taxa of the group, not its occurrences
- the cached summary is refreshed (debounced) when group taxa or site
  settings change
- total_species / total_subspecies breakdown is only added when that
  setting is enabled
"""
from unittest.mock import patch

from django_tenants.test.cases import FastTenantTestCase
from preferences import preferences

from bims.api_views.module_summary import ModuleSummary
from bims.enums.taxonomic_group_category import TaxonomicGroupCategory
from bims.enums.taxonomic_rank import TaxonomicRank
from bims.enums.taxonomic_status import TaxonomicStatus
from bims.models import BiologicalCollectionRecord
from bims.models.site_setting import SiteSetting
from bims.tests.model_factories import (
    TaxonomyF,
    TaxonGroupF,
    TaxonGroupTaxonomyF,
    BiologicalCollectionRecordF,
    IUCNStatusF,
)


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
        TaxonGroupTaxonomyF.create(
            taxongroup=self.parent, taxonomy=self.parent_taxon, is_validated=True
        )

        # Child group with 1 unique accepted species
        self.child = _species_group('Child Fish', parent=self.parent)
        self.child_taxon = _accepted(scientific_name='ChildFish')
        TaxonGroupTaxonomyF.create(
            taxongroup=self.child, taxonomy=self.child_taxon, is_validated=True
        )

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
            taxongroup=self.parent, taxonomy=self.child_taxon, is_validated=True
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
        TaxonGroupTaxonomyF.create(
            taxongroup=self.group, taxonomy=self.taxon_with_fada, is_validated=True
        )
        TaxonGroupTaxonomyF.create(
            taxongroup=self.group, taxonomy=self.taxon_no_fada, is_validated=True
        )

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
            TaxonGroupTaxonomyF.create(
                taxongroup=self.group, taxonomy=t, is_validated=True
            )

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
        TaxonGroupTaxonomyF.create(
            taxongroup=self.parent, taxonomy=self.p_taxon, is_validated=True
        )

        # child group: one fada, one not
        self.child = _species_group('Sub-reptiles', parent=self.parent)
        self.c_fada = _accepted(scientific_name='ChildReptileA', fada_id='R002')
        self.c_no_fada = _accepted(scientific_name='ChildReptileB', fada_id='')
        TaxonGroupTaxonomyF.create(
            taxongroup=self.child, taxonomy=self.c_fada, is_validated=True
        )
        TaxonGroupTaxonomyF.create(
            taxongroup=self.child, taxonomy=self.c_no_fada, is_validated=True
        )

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
        TaxonGroupTaxonomyF.create(
            taxongroup=self.group, taxonomy=self.accepted, is_validated=True
        )
        TaxonGroupTaxonomyF.create(
            taxongroup=self.group, taxonomy=self.synonym, is_validated=True
        )

    @patch('bims.api_views.module_summary.is_fada_site', return_value=False)
    def test_only_accepted_counted(self, _mock):
        count = self.ms._validated_count_for_group(self.group)
        self.assertEqual(count, 1)


def _set_conservation_status_use_taxon_count(value):
    """Toggle the SiteSetting singleton flag, creating it if needed."""
    site_setting = preferences.SiteSetting
    if not site_setting:
        site_setting = SiteSetting.objects.create()
    site_setting.conservation_status_chart_use_taxon_count = value
    site_setting.save()


class TestConservationStatusSummaryCounting(FastTenantTestCase):
    """By default the conservation status chart counts occurrence records;
    when conservation_status_chart_use_taxon_count is enabled it counts
    distinct taxa instead."""

    def setUp(self):
        self.ms = ModuleSummary()
        self.iucn_status = IUCNStatusF.create(category='LC', national=False)
        self.taxon = TaxonomyF.create(
            scientific_name='Repeated Fish',
            rank=TaxonomicRank.SPECIES.name,
            iucn_status=self.iucn_status,
        )
        # Same taxon collected 3 times -> 3 occurrence records, 1 distinct taxon
        for _ in range(3):
            BiologicalCollectionRecordF.create(taxonomy=self.taxon)
        self.collections = BiologicalCollectionRecord.objects.filter(
            taxonomy=self.taxon
        )

    def tearDown(self):
        _set_conservation_status_use_taxon_count(False)

    def test_default_counts_occurrence_records(self):
        _set_conservation_status_use_taxon_count(False)
        summary = self.ms.get_conservation_status_summary(self.collections)
        self.assertEqual(summary['chart_data']['Least Concern'], 3)

    def test_enabled_counts_distinct_taxa(self):
        _set_conservation_status_use_taxon_count(True)
        summary = self.ms.get_conservation_status_summary(self.collections)
        self.assertEqual(summary['chart_data']['Least Concern'], 1)


class TestModuleSummarySpeciesSubspeciesBreakdown(FastTenantTestCase):
    """total_species / total_subspecies are only added, and only counted
    per distinct taxon, when conservation_status_chart_use_taxon_count is
    enabled."""

    def setUp(self):
        self.ms = ModuleSummary()
        self.group = _species_group('Mammals')

        self.species_taxon = TaxonomyF.create(
            scientific_name='SpeciesA',
            rank=TaxonomicRank.SPECIES.name,
        )
        self.subspecies_taxon = TaxonomyF.create(
            scientific_name='SubspeciesA',
            rank=TaxonomicRank.SUBSPECIES.name,
        )
        self.genus_taxon = TaxonomyF.create(
            scientific_name='GenusA',
            rank=TaxonomicRank.GENUS.name,
        )
        for taxon in (
            self.species_taxon, self.subspecies_taxon, self.genus_taxon
        ):
            TaxonGroupTaxonomyF.create(taxongroup=self.group, taxonomy=taxon)

        # Multiple occurrence records per taxon to prove distinct counting
        BiologicalCollectionRecordF.create(taxonomy=self.species_taxon)
        BiologicalCollectionRecordF.create(taxonomy=self.species_taxon)
        BiologicalCollectionRecordF.create(taxonomy=self.subspecies_taxon)
        BiologicalCollectionRecordF.create(taxonomy=self.genus_taxon)

    def tearDown(self):
        _set_conservation_status_use_taxon_count(False)

    def test_breakdown_absent_when_disabled(self):
        _set_conservation_status_use_taxon_count(False)
        data = self.ms.module_summary_data(self.group)
        self.assertNotIn('total_species', data)
        self.assertNotIn('total_subspecies', data)

    def test_breakdown_present_and_correct_when_enabled(self):
        _set_conservation_status_use_taxon_count(True)
        data = self.ms.module_summary_data(self.group)
        self.assertEqual(data['total_species'], 1)
        self.assertEqual(data['total_subspecies'], 1)

    def test_genus_rank_excluded_from_breakdown(self):
        _set_conservation_status_use_taxon_count(True)
        data = self.ms.module_summary_data(self.group)
        # Only SPECIES/SUBSPECIES ranks are counted, GENUS is not
        self.assertEqual(
            data['total_species'] + data['total_subspecies'], 2
        )


class TestConservationStatusTaxonCountIndependentOfOccurrences(
        FastTenantTestCase):
    """With the taxon count option the chart uses the taxa of the group,
    including the taxa without any occurrence."""

    def setUp(self):
        self.ms = ModuleSummary()
        self.group = _species_group('Reptiles')
        lc = IUCNStatusF.create(category='LC', national=False)
        with_records = TaxonomyF.create(
            scientific_name='Has Records',
            rank=TaxonomicRank.SPECIES.name, iucn_status=lc)
        no_records = TaxonomyF.create(
            scientific_name='No Records',
            rank=TaxonomicRank.SPECIES.name, iucn_status=lc)
        for taxon in (with_records, no_records):
            TaxonGroupTaxonomyF.create(taxongroup=self.group, taxonomy=taxon)
        BiologicalCollectionRecordF.create(taxonomy=with_records)

    def tearDown(self):
        _set_conservation_status_use_taxon_count(False)

    def test_chart_counts_taxa_without_occurrences(self):
        _set_conservation_status_use_taxon_count(True)
        self.group.chart_data = 'conservation status'
        data = self.ms.module_summary_data(self.group)
        self.assertEqual(
            data['conservation-status']['chart_data']['Least Concern'], 2)
        self.assertEqual(data['total_species'], 2)


class TestConservationStatusTaxonCountGroupScope(FastTenantTestCase):
    """The taxon count chart only uses the taxa of its own group, counts
    NE for taxa without an IUCN status and ignores occurrences."""

    def setUp(self):
        self.ms = ModuleSummary()
        self.group = _species_group('Birds')
        self.other_group = _species_group('Frogs')
        lc = IUCNStatusF.create(category='LC', national=False)
        self.lc_taxon = TaxonomyF.create(
            scientific_name='Bird LC',
            rank=TaxonomicRank.SPECIES.name, iucn_status=lc)
        self.ne_taxon = TaxonomyF.create(
            scientific_name='Bird NE', rank=TaxonomicRank.SPECIES.name)
        self.other_taxon = TaxonomyF.create(
            scientific_name='Frog LC',
            rank=TaxonomicRank.SPECIES.name, iucn_status=lc)
        TaxonGroupTaxonomyF.create(
            taxongroup=self.group, taxonomy=self.lc_taxon)
        TaxonGroupTaxonomyF.create(
            taxongroup=self.group, taxonomy=self.ne_taxon)
        TaxonGroupTaxonomyF.create(
            taxongroup=self.other_group, taxonomy=self.other_taxon)
        # Many occurrences of one taxon must not inflate the count
        for _ in range(3):
            BiologicalCollectionRecordF.create(taxonomy=self.lc_taxon)

    def tearDown(self):
        _set_conservation_status_use_taxon_count(False)

    def _chart(self, **kwargs):
        collections = BiologicalCollectionRecord.objects.filter(
            taxonomy__in=self.group.taxonomies.all())
        return self.ms.get_conservation_status_summary(
            collections, **kwargs)['chart_data']

    def test_counts_only_taxa_of_the_group(self):
        _set_conservation_status_use_taxon_count(True)
        self.assertEqual(
            self._chart(taxon_group=self.group), {'Least Concern': 1})

    def test_default_still_counts_occurrences_with_group_given(self):
        _set_conservation_status_use_taxon_count(False)
        self.assertEqual(
            self._chart(taxon_group=self.group), {'Least Concern': 3})

    def test_group_without_occurrences_still_has_chart(self):
        _set_conservation_status_use_taxon_count(True)
        self.assertEqual(
            self._chart(taxon_group=self.other_group), {'Least Concern': 1})

    def test_species_totals_independent_of_occurrences(self):
        _set_conservation_status_use_taxon_count(True)
        data = self.ms.module_summary_data(self.other_group)
        self.assertEqual(data['total'], 0)
        self.assertEqual(data['total_species'], 1)


class TestModuleSummaryRefreshTriggers(FastTenantTestCase):
    """The cached module summary is regenerated when the taxa of a group or
    the site settings change, and bursts are collapsed into one task."""

    def setUp(self):
        from django.core.cache import cache
        self.cache = cache
        self.key = 'module_summary_refresh_{}'.format(
            self.get_test_schema_name())
        self.cache.delete(self.key)

    def tearDown(self):
        self.cache.delete(self.key)

    def test_queue_is_debounced(self):
        from bims.tasks.module_summary import queue_module_summary_refresh
        with self.settings(TESTING=False), patch(
                'bims.tasks.module_summary.generate_module_summary'
        ) as task, patch('bims.tasks.module_summary.connection') as conn:
            conn.schema_name = self.get_test_schema_name()
            queue_module_summary_refresh()
            queue_module_summary_refresh()
        self.assertEqual(task.apply_async.call_count, 1)

    def test_queue_skipped_when_testing(self):
        with patch(
                'bims.tasks.module_summary.generate_module_summary'
        ) as task:
            from bims.tasks.module_summary import (
                queue_module_summary_refresh
            )
            queue_module_summary_refresh()
        task.apply_async.assert_not_called()

    def test_taxon_group_taxonomy_change_queues_refresh(self):
        group = _species_group('Insects')
        taxon = _accepted(scientific_name='Bug')
        with patch(
                'bims.tasks.module_summary.queue_module_summary_refresh'
        ) as queue:
            link = TaxonGroupTaxonomyF.create(
                taxongroup=group, taxonomy=taxon)
            queue.assert_called()
            queue.reset_mock()
            link.delete()
            queue.assert_called()

    def test_site_setting_save_queues_refresh(self):
        with patch(
                'bims.tasks.module_summary.queue_module_summary_refresh'
        ) as queue:
            _set_conservation_status_use_taxon_count(True)
            _set_conservation_status_use_taxon_count(False)
        self.assertGreaterEqual(queue.call_count, 2)
