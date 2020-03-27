from scripts.management.commands.import_algae_species import Command as BaseCommand
from bims.models import Endemism, TaxonGroup, TaxonomicGroupCategory


ENDEMISM = 'Endemism'
ORIGIN = 'Origin'


class Command(BaseCommand):

    def csv_file_name(self, options):
        self.import_date = options.get('import_date', None)
        return 'SA Invertebrate Master List FBISv3_27 Mar 2020.csv'

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

        # -- Import date
        data['Import Date'] = self.import_date
        taxonomy.additional_data = data

        # -- Add Genus to Algae taxon group
        taxon_group, _ = TaxonGroup.objects.get_or_create(
            name='Invertebrates',
            category=TaxonomicGroupCategory.SPECIES_MODULE.name
        )
        if taxonomy.rank == 'SPECIES' and taxonomy.parent:
            taxon_group.taxonomies.add(taxonomy.parent)
        elif taxonomy.rank == 'SUBSPECIES' and taxonomy.parent and taxonomy.parent.parent:
            taxon_group.taxonomies.add(taxonomy.parent.parent)
        else:
            taxon_group.taxonomies.add(taxonomy)

        taxonomy.additional_data = data
        taxonomy.save()
