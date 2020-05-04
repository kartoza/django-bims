from scripts.management.commands.import_species import Command as BaseCommand
from bims.models import (
    Endemism, TaxonGroup, TaxonomicGroupCategory, IUCNStatus
)


ECO_TOLERANCE = 'Eco-tolerance'
ENDEMISM = 'Endemism'
ORIGIN = 'Origin'
CONSERVATION_STATUS = 'Conservation status'


class Command(BaseCommand):

    def csv_file_name(self, options):
        return 'fish_master_list.csv'

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
            if 'non-native' in row[ORIGIN].lower():
                taxonomy.origin =  'alien'
            else:
                taxonomy.origin = 'indigenous'

        # -- ECO tolerance
        if row[ECO_TOLERANCE]:
            data[ECO_TOLERANCE] = row[ECO_TOLERANCE]

        # -- Conservation status
        if row[CONSERVATION_STATUS] and not taxonomy.iucn_status:
            categories = dict(IUCNStatus.CATEGORY_CHOICES)
            for iucn_category in categories:
                if categories[iucn_category].lower() == row[CONSERVATION_STATUS].lower().strip():
                    try:
                        iucn = IUCNStatus.objects.get(
                            category=iucn_category
                        )
                    except IUCNStatus.DoesNotExist:
                        iucn = IUCNStatus.objects.get(
                            category='DD'
                        )
                    taxonomy.iucn_status = iucn

        # -- Add species to Fish taxon group
        taxon_group, _ = TaxonGroup.objects.get_or_create(
            name='Fish',
            category=TaxonomicGroupCategory.SPECIES_MODULE.name
        )
        taxon_group.taxonomies.add(taxonomy)

        taxonomy.additional_data = data
        taxonomy.save()
