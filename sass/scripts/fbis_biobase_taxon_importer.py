from sass.scripts.fbis_postgres_importer import FbisPostgresImporter
from bims.utils.gbif import search_taxon_identifier
from biobase.models import BioTaxon


class FbisBiobaseTaxonImporter(FbisPostgresImporter):

    table_name = 'public."BioTaxon"'
    content_type_model = BioTaxon
    species_ranks = [
        'GenusSpecies',
        'SubFamily',
        'Family',
        'SubOrder',
        'Order',
        'Class',
        'Phylum',
    ]

    def process_row(self, row, index):
        current_species_rank = 0
        taxon_name = self.get_row_value('Taxon')
        note = self.get_row_value('Note')

        species = self.get_row_value(
            self.species_ranks[current_species_rank]
        )
        while (
                species.lower() == 'unspecified' and
                current_species_rank < len(self.species_ranks)
        ):
            current_species_rank += 1
            species = self.get_row_value(
                self.species_ranks[current_species_rank]
            )

        taxonomy = search_taxon_identifier(species)
        while not taxonomy and current_species_rank < len(self.species_ranks):
            current_species_rank += 1
            taxonomy = search_taxon_identifier(self.get_row_value(
                self.species_ranks[current_species_rank]
            ))

        if not taxonomy:
            print('taxonomy not found')
            return

        bio_taxon, created = BioTaxon.objects.get_or_create(
            bio_taxon_name=taxon_name,
            taxonomy=taxonomy,
            note=note
        )
        self.save_uuid(
            uuid=self.get_row_value('BioTaxonID'),
            object_id=bio_taxon.id
        )
