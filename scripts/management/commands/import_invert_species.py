from scripts.management.commands.import_species import Command as BaseCommand
from bims.models import Endemism, TaxonGroup, TaxonomicGroupCategory


ENDEMISM = 'Endemism'
ORIGIN = 'Origin'


class Command(BaseCommand):

    def csv_file_name(self, options):
        return 'invert_master_list.csv'

    def rank_classifier(self):
        return {'kingdom': 'Animalia'}

    def additional_data(self, taxonomy, row):
        """
        Import additional data from CSV into taxonomy.
        :param taxonomy: Taxonomy object
        :param row: data row from csv
        """
        data = dict()

        # -- Endemism
        if ENDEMISM in row and row[ENDEMISM]:
            endemism, _ = Endemism.objects.get_or_create(
                name=row[ENDEMISM]
            )
            taxonomy.endemism = endemism

        # -- Origin
        if row[ORIGIN]:
            data[ORIGIN] = row[ORIGIN]

        # -- Add species to invert taxon group
        taxon_group, _ = TaxonGroup.objects.get_or_create(
            name__icontains='invertebrate',
            category=TaxonomicGroupCategory.SPECIES_MODULE.name
        )
        taxon_group.taxonomies.add(taxonomy)

        taxonomy.additional_data = data
        taxonomy.save()
