import csv
import os
from bims.utils.fetch_gbif import fetch_all_species_from_gbif

FISH_FILE = 'SA.Master.fish.species.csv'

SCIENTIFIC_NAME_KEY = 'Scientific name and authority'
CANONICAL_NAME_KEY = 'Taxon'
COMMON_NAME_KEY = 'Common name'


def import_fish_species_from_file(fish_file=FISH_FILE):
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

    i = 0

    scientific_name = fish_data[SCIENTIFIC_NAME_KEY][i]
    canonical_name = fish_data[CANONICAL_NAME_KEY][i]
    common_name = fish_data[COMMON_NAME_KEY][i]

    fetch_all_species_from_gbif(
        species=canonical_name,
        should_get_children=False
    )
