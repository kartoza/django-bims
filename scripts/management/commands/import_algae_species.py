import os
import logging
from django.db.models import signals
from scripts.management.csv_command import CsvCommand
from bims.utils.fetch_gbif import fetch_all_species_from_gbif
from bims.utils.logger import log
from bims.utils.gbif import *
from bims.models.taxon_group import TaxonGroup, TaxonomicGroupCategory
from bims.models.taxonomy import taxonomy_pre_save_handler

logger = logging.getLogger('bims')

IN_GBIF = 'In GBIF'
TAXON = 'Taxon'
SPECIES = 'Species'
GENUS = 'Genus'
FAMILY = 'Family'
ORDER = 'Order'
DIVISION = 'Division'
GROWTH_FORM = 'Growth Form'


class Command(CsvCommand):

    def add_arguments(self, parser):
        parser.add_argument(
            '-d',
            '--import-data',
            dest='import_date',
            default=None,
            help='Date of the import'
        )

    def csv_file_name(self, options):
        self.import_date = options.get('import_date', None)
        return 'SA Algal Master List FBISv3_3 Mar 2020.csv'

    @property
    def csv_root_folder(self):
        dev_folder = '/home/web/django_project'
        folder_name = 'data'
        if os.path.exists(dev_folder):
            root = dev_folder
        else:
            root = '/usr/src/bims'
        return os.path.join(
            root,
            'scripts/static/{}/'.format(
                folder_name
            )
        )

    def additional_data(self, taxonomy, row):
        """
        Import additional data from CSV into taxonomy.
        :param taxonomy: Taxonomy object
        :param row: data row from csv
        """
        data = dict()

        # -- Division
        if DIVISION in row:
            data[DIVISION] = row[DIVISION]

        # -- Growth Form
        if GROWTH_FORM in row:
            data[GROWTH_FORM] = row[GROWTH_FORM]

        # -- Import date
        data['Import Date'] = self.import_date

        # -- Add Genus to Algae taxon group
        taxon_group, _ = TaxonGroup.objects.get_or_create(
            name='Algae',
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

    def csv_dict_reader(self, csv_reader):
        signals.pre_save.disconnect(
            taxonomy_pre_save_handler,
            sender=Taxonomy
        )
        errors = []
        success = []

        index = 2

        for row in csv_reader:
            try:
                print('---------')
                # Get rank
                if row[SPECIES]:
                    rank = SPECIES
                elif row[GENUS]:
                    rank = GENUS
                else:
                    rank = FAMILY

                taxa = Taxonomy.objects.filter(
                    canonical_name__iexact=row[TAXON],
                    rank=rank.upper()
                )
                taxonomy = None
                if taxa.exists():
                    taxonomy = taxa[0]
                    logger.debug('{} already exists in the system'.format(
                        row[TAXON]
                    ))

                if not taxonomy:
                    # Fetch from gbif
                    taxonomy = fetch_all_species_from_gbif(
                        species=row[TAXON],
                        taxonomic_rank=rank,
                        should_get_children=False,
                        fetch_vernacular_names=False,
                        use_name_lookup=False
                    )
                if taxonomy:
                    success.append(taxonomy.id)
                else:
                    # Try again with lookup
                    logger.debug('Use different method')
                    taxonomy = fetch_all_species_from_gbif(
                        species=row[TAXON],
                        taxonomic_rank=rank,
                        should_get_children=False,
                        fetch_vernacular_names=False,
                        use_name_lookup=True
                    )
                    if not taxonomy:
                        errors.append({
                            'row': index,
                            'error': 'Taxonomy not found'
                        })
                    else:
                        success.append(taxonomy.id)

                # Data from GBIF couldn't be found, so add it manually
                if not taxonomy:
                    # Find genus
                    parent = fetch_all_species_from_gbif(
                        species=row[GENUS],
                        taxonomic_rank='Genus',
                        should_get_children=False,
                        fetch_vernacular_names=False
                    )
                    # Find family
                    if not parent:
                        parent = fetch_all_species_from_gbif(
                            species=row[FAMILY],
                            taxonomic_rank='Family',
                            should_get_children=False,
                            fetch_vernacular_names=False
                        )
                    if not parent:
                        errors.append({
                            'row': index,
                            'error': 'Parent not found {}'.format(
                                row[TAXON]
                            )
                        })
                    else:
                        taxonomy, create = Taxonomy.objects.get_or_create(
                            scientific_name=row[TAXON],
                            canonical_name=row[TAXON],
                            rank=TaxonomicRank[rank.upper()].name,
                            parent=parent
                        )
                        success.append(taxonomy.id)

                if taxonomy:
                    self.additional_data(
                        taxonomy,
                        row
                    )
            except Exception as e:  # noqa
                print(str(e))
                errors.append({
                    'row': index,
                    'error': str(e)
                })

            index += 1

        if len(errors) > 0: logger.debug(errors)
        log('----')
        if len(success) > 0: logger.debug(success)
