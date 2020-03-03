from scripts.management.commands.import_algae_species import Command as BaseCommand
from bims.models import Endemism


ENDEMISM = 'Endemism'
ORIGIN = 'Origin'


class Command(BaseCommand):

    def csv_file_name(self, options):
        self.import_date = options.get('import_date', None)
        return 'SA Invertebrate Master List FBISv3_03 Mar 2020.csv'

    def additional_data(self, taxonomy, row):
        """
        Import additional data from CSV into taxonomy.
        :param taxonomy: Taxonomy object
        :param row: data row from csv
        """
        data = dict()

        # -- Endemism
        if ENDEMISM in row and row[ENDEMISM]:
            endemism = Endemism.objects.get_or_create(
                name=row[ENDEMISM]
            )
            taxonomy.endemism = endemism

        # -- Origin
        if row[ORIGIN]:
            data[ORIGIN] = row[ORIGIN]

        # -- Import date
        data['Import Date'] = self.import_date

        taxonomy.additional_data = data

        taxonomy.save()
