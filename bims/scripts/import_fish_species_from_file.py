import csv
import os
import logging
from bims.utils.fetch_gbif import fetch_all_species_from_gbif
from bims.scripts.import_gbif_occurrences import import_gbif_occurrences
from bims.models import IUCNStatus, Endemism

FISH_FILE = 'SA.Master.fish.species.csv'

SCIENTIFIC_NAME_KEY = 'Scientific name and authority'
CANONICAL_NAME_KEY = 'Taxon'
COMMON_NAME_KEY = 'Common name'
CONSERVATION_STATUS_KEY = 'Conservation status'
HABITAT_KEY = 'Habitat'
ORIGIN_KEY = 'Origin'
ENDEMISM_KEY = 'Endemism'

logger = logging.getLogger('bims')


def import_fish_species_from_file(
    import_occurrences=False,
    fish_file=FISH_FILE):
    """
    Read fish list from a file then fetch the data from GBIF.
    :param fish_file: Fish species file to read
    :param import_occurrences: Should also import occurrences or not
    """
    folder_name = 'data'
    file_path = os.path.join(
        os.path.abspath(os.path.dirname(__name__)),
        'bims/static/{folder}/{filename}'.format(
            folder=folder_name,
            filename=fish_file
        ))

    data_length = 0
    fish_data = {}

    with open(file_path) as csv_file:
        reader = csv.reader(csv_file)
        rows = [row for row in reader if row]
        headings = rows[0]
        for row in rows[1:]:
            data_length += 1
            for col_header, data_column in zip(headings, row):
                fish_data.setdefault(col_header, []).append(
                    data_column)

    for i in range(data_length):
        canonical_name = fish_data[CANONICAL_NAME_KEY][i]
        endemism_value = fish_data[ENDEMISM_KEY][i]

        taxonomy = fetch_all_species_from_gbif(
            species=canonical_name,
            should_get_children=True
        )

        if not taxonomy:
            continue

        endemism, endemism_created = Endemism.objects.get_or_create(
            name=endemism_value
        )
        taxonomy.endemism = endemism
        taxonomy.save()

        conservation_status = fish_data[CONSERVATION_STATUS_KEY][i]
        for category in IUCNStatus.CATEGORY_CHOICES:
            if category[1].lower() == conservation_status.lower():
                iucn_status = IUCNStatus.objects.filter(
                    category=category[0]
                )
                if len(iucn_status) < 1:
                    break
                logger.info('Add IUCN status : %s' %
                            iucn_status[0].get_category_display())
                taxonomy.iucn_status = iucn_status[0]
                taxonomy.save()

        if import_occurrences:
            import_gbif_occurrences(
                taxonomy=taxonomy,
                origin=fish_data[ORIGIN_KEY][i],
                habitat=fish_data[HABITAT_KEY][i]
            )
