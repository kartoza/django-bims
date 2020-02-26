import csv
from django.core.management.base import BaseCommand
from django.db.models import Q
from bims.models import *

TAXON = 'Taxon'
SCIENTIFIC_NAME_AND_AUTHORITY = 'Scientific name and authority'
COMMON_NAME = 'Common name'
HABITAT = 'Habitat'
ORIGIN = 'Origin'
ENDEMISM = 'Endemism'
CONSERVATION_STATUS = 'Conservation status'


class Command(BaseCommand):

    file_name = 'SA Master fish species list_15 Nov 2019_FINAL.csv'

    def handle(self, *args, **options):
        dev_folder = '/home/web/django_project'
        folder_name = 'data'
        if os.path.exists(dev_folder):
            root = dev_folder
        else:
            root = '/usr/src/bims'
        csv_file_path = os.path.join(
            root,
            'scripts/static/{folder}/{filename}'.format(
                folder=folder_name,
                filename=self.file_name
            )
        )
        not_updated = []

        # Delete all vernacular names
        VernacularName.objects.all().delete()

        with open(csv_file_path) as csv_file:
            csv_reader = csv.DictReader(csv_file)
            for row in csv_reader:
                taxa = Taxonomy.objects.filter(
                    Q(scientific_name__icontains=row[TAXON]) |
                    Q(canonical_name__icontains=row[TAXON])
                )
                if not taxa.exists():
                    not_updated.append(row[TAXON])
                    continue
                if row[COMMON_NAME]:
                    vernacular_names = VernacularName.objects.filter(
                        name__icontains=row[COMMON_NAME],
                        language='en'
                    )
                    if vernacular_names.exists():
                        common_name = vernacular_names[0]
                    else:
                        common_name = VernacularName.objects.create(
                            name=row[COMMON_NAME],
                            source='SA Master fish species list FBIS',
                            language='en'
                        )
                    for taxon in taxa:
                        taxon.vernacular_names.add(common_name)

        print ('Not updated ({length}) : {list}'.format(
            length=len(not_updated),
            list=','.join(not_updated)))
