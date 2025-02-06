from django.test import TestCase

from bims.enums import TaxonomicGroupCategory
from bims.tests.model_factories import (
    TaxonomyF, BiologicalCollectionRecordF, TaxonGroupF, VernacularNameF
)
from bims.utils.fetch_gbif import merge_taxa_data
from bims.models import Taxonomy, BiologicalCollectionRecord, TaxonGroup, IUCNStatus, TaxonExtraAttribute
from bims.views.download_csv_taxa_list import TaxaCSVSerializer


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
            gbif_key='12345',
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
            'subspecies', 'taxon', 'scientific_name_and_authority', 'common_name', 'origin',
            'endemism', 'conservation_status_global', 'conservation_status_national', 'on_gbif', 'gbif_link',
            'Growth form', 'freshwater', 'testing', 'ANT'
        ]

        for field in expected_fields:
            self.assertIn(field, serialized_data)

    def test_serializer_values(self):
        serializer = TaxaCSVSerializer(instance=self.taxonomy)
        serialized_data = serializer.data

        self.assertEqual(serialized_data['taxon_rank'], 'Species')
        self.assertEqual(serialized_data['species'], 'Homo sapiens')
        self.assertEqual(serialized_data['taxon'], 'Homo sapiens')
        self.assertEqual(serialized_data['scientific_name_and_authority'], 'Homo sapiens Linnaeus')
        self.assertEqual(serialized_data['common_name'], 'Human')
        self.assertEqual(serialized_data['endemism'], 'Unknown')
        self.assertEqual(serialized_data['conservation_status_global'], 'Least Concern')
        self.assertEqual(serialized_data['conservation_status_national'], 'Near Threatened')
        self.assertEqual(serialized_data['on_gbif'], 'Yes')
        self.assertEqual(serialized_data['gbif_link'], 'https://www.gbif.org/species/12345')
        self.assertEqual(serialized_data['Growth form'], 'Tree')
        self.assertEqual(serialized_data['freshwater'], 'Y')
        self.assertEqual(serialized_data['testing'], 'Y')
        self.assertEqual(serialized_data['ANT'], 'Y')
        self.assertEqual(serialized_data['TEST'], '?')
        self.assertTrue(len(serializer.context.get('tags')) > 0)
