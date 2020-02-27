import os
import logging
from scripts.management.csv_command import CsvCommand
from bims.utils.fetch_gbif import fetch_all_species_from_gbif
from bims.utils.logger import log
from bims.utils.gbif import *

logger = logging.getLogger('bims')

IN_GBIF = 'In GBIF'
TAXON_RANK = 'Taxon rank'
TAXON = 'Taxon'
GENUS = 'Genus'
FAMILY = 'Family'
ORDER = 'Order'


class Command(CsvCommand):

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

    def csv_dict_reader(self, csv_reader):
        errors = []
        success = []

        index = 2

        for row in csv_reader:
            try:
                if row[IN_GBIF] == 'Yes':
                    # Fetch from gbif
                    taxonomy = fetch_all_species_from_gbif(
                        species=row[TAXON],
                        taxonomic_rank=row[TAXON_RANK],
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
                            taxonomic_rank=row[TAXON_RANK],
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
                else:
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
                            rank=TaxonomicRank[row[TAXON_RANK].upper()].name,
                            parent=parent
                        )
                        success.append(taxonomy.id)
            except Exception as e:  # noqa
                errors.append({
                    'row': index,
                    'error': str(e)
                })

            index += 1

        if len(errors) > 0: logger.debug(errors)
        log('----')
        if len(success) > 0: logger.debug(success)
