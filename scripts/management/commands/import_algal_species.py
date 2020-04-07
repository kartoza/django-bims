import copy
from scripts.management.commands.import_species import (
    Command as BaseCommand, ALL_TAXON_RANKS
)
from bims.models import Endemism, TaxonGroup, TaxonomicGroupCategory


ENDEMISM = 'Endemism'
ORIGIN = 'Origin'
DIVISION = 'Division'
GROWTH_FORM = 'Growth form'


class Command(BaseCommand):

    def csv_file_name(self, options):
        return 'sa_algal_species_list_27_mar.csv'

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

        # -- Growth form
        if row[GROWTH_FORM]:
            data[GROWTH_FORM] = row[GROWTH_FORM]

        # -- Add Genus to Algae taxon group
        taxon_group, _ = TaxonGroup.objects.get_or_create(
            name='Algae',
            category=TaxonomicGroupCategory.SPECIES_MODULE.name
        )

        # -- Division group
        division_group = None
        if row[DIVISION]:
            division_group, _ = TaxonGroup.objects.get_or_create(
                name=row[DIVISION],
                category=TaxonomicGroupCategory.DIVISION_GROUP.name
            )

        taxon_group.taxonomies.add(taxonomy)
        if division_group:
            division_group.taxonomies.add(taxonomy)

        taxonomy.additional_data = data
        taxonomy.save()
