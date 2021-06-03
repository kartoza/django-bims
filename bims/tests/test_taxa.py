from django.test import TestCase
from bims.tests.model_factories import (
    TaxonomyF, BiologicalCollectionRecordF, TaxonGroupF, VernacularNameF
)
from bims.utils.fetch_gbif import merge_taxa_data
from bims.models import Taxonomy, BiologicalCollectionRecord, TaxonGroup


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
