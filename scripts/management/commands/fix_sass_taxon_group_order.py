import csv
import os
from django.db.models import Q
from django.core.management.base import BaseCommand

from bims.utils.logger import log
from bims.models import TaxonGroup
from sass.models.sass_taxon import SassTaxon

TAXON_GROUP = 'Taxon Group'
TAXON = 'Taxon'


class Command(BaseCommand):

    file_name = 'sass_taxa_group.csv'

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

        if not os.path.exists(csv_file_path):
            log('File not found')

        with open(csv_file_path) as csv_file:
            csv_reader = csv.DictReader(csv_file)
            current_taxon_group = None
            for row in csv_reader:
                taxon_group_name = row[TAXON_GROUP]
                if taxon_group_name:
                    current_taxon_group = TaxonGroup.objects.get(
                        name__iexact=taxon_group_name
                    )
                sass_taxa = SassTaxon.objects.filter(
                    Q(taxon_sass_5__iexact=row[TAXON]) |
                    Q(taxon_sass_4__iexact=row[TAXON])
                )
                if sass_taxa.exists():
                    if not current_taxon_group.taxonomies.filter(
                        id__in=sass_taxa.values_list('taxon_id')
                    ).exists():
                        log('Sass taxon does not in the correct group')
                        current_taxon_group.taxonomies.add(sass_taxa[0].taxon)
                else:
                    log('Sass Taxon does not exist')