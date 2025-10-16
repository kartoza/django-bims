import os
import json
from unittest.mock import patch
from django.test import TestCase

from bims.models import Taxonomy
from bims.scripts.species_keys import *  # noqa
from bims.scripts.taxa_upload import TaxaProcessor
from bims.tests.model_factories import TaxonomyF, BiologicalCollectionRecordF, \
    TaxonGroupF
from scripts.fixes.fix_taxa_without_module import fix_taxa_without_modules
from scripts.virtual_museum import TaxaDarwinCore

test_data_directory = os.path.join(
    os.path.dirname(os.path.realpath(__file__)).replace('scripts', 'bims'),
    'data')

def mocked_gbif_data():
    class MockResponse:
        def __init__(self, json_data, status_code):
            self.json_data = json_data
            self.status_code = status_code

        def json(self):
            return self.json_data

class TestScript(TestCase):
    def test_fix_taxa_without_module(self):
        taxon_group = TaxonGroupF.create(
            name='invert'
        )
        taxon = TaxonomyF.create(
            scientific_name='Test'
        )
        BiologicalCollectionRecordF.create(
            taxonomy=taxon,
            module_group=taxon_group
        )
        self.assertEqual(len(taxon.taxongroup_set.all()), 0)
        fix_taxa_without_modules()

        taxon = Taxonomy.objects.get(id=taxon.id)
        self.assertEqual(taxon.taxongroup_set.first(), taxon_group)

    @patch.object(TaxaProcessor, 'validate_parents')
    def test_virtual_museum_harvester(self, mock_validate_parents):
        occurrences_file = os.path.join(
            test_data_directory, 'gbif_occurrences.json')
        taxon_group = TaxonGroupF.create(
            name='invert'
        )
        species_data = []
        kingdom = TaxonomyF.create(
            rank='KINGDOM',
            canonical_name='TEST',
            gbif_key=2
        )
        TaxonomyF.create(
            rank='GENUS',
            canonical_name='Pseudobarbus',
            gbif_key=1,
            parent=kingdom
        )
        with open(occurrences_file) as file:
            data = json.load(file)
            for result in data['results']:
                taxon_rank = result['taxonRank'].lower()
                if taxon_rank == 'species':
                    species_name = '{genus} {spc}'.format(
                        genus=result['genus'],
                        spc=result['specificEpithet']
                    )
                else:
                    if 'sub' in taxon_rank:
                        taxon_rank = taxon_rank.replace('sub', '')
                    species_name = result[taxon_rank]
                species_data.append({
                    ON_GBIF: 'No',
                    KINGDOM: result['kingdom'],
                    PHYLUM: result['phylum'],
                    CLASS: result['class'],
                    ORDER: result['order'],
                    FAMILY: result['family'],
                    GENUS: result['genus'],
                    SCIENTIFIC_NAME: result["scientificName"],
                    CONSERVATION_STATUS: result['iucnRedListCategory'],
                    TAXON_RANK: result['taxonRank'],
                    TAXON: species_name,
                    "TAXON_ID": result['taxonID']
                })

        mock_validate_parents.return_value = True, ''
        TaxaDarwinCore(species_data[:1], taxon_group)
        taxa = Taxonomy.objects.filter(
            canonical_name=species_data[:1][0][TAXON]
        )
        self.assertTrue(taxa.exists())
        self.assertEqual(taxa.first().taxongroup_set.first(), taxon_group)
