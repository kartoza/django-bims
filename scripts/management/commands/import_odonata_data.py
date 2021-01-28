import os
import time
import logging
import uuid
import csv
import json
import ast
import requests
import zipfile
from dwca.read import DwCAReader
from django.core.management import BaseCommand
from django.contrib.contenttypes.models import ContentType
from django.conf import settings
from bims.scripts.collection_csv_keys import *  # noqa
from bims.scripts.species_keys import *  # noqa
from bims.scripts.taxa_upload import TaxaProcessor
from bims.models.biological_collection_record import BiologicalCollectionRecord
from bims.scripts.occurrences_upload import OccurrenceProcessor
from bims.models.taxon_group import TaxonGroup, TaxonomicGroupCategory
from bims.models.ingested_data import IngestedData

logger = logging.getLogger('bims')

ALL_DATA = 'ALL_DATA'
TAXON_ID = 'TAXON_ID'


class TaxaDarwinCore(TaxaProcessor):

    def handle_error(self, row, message):
        print('ERROR')
        print(message)

    def finish_processing_row(self, row, taxonomy):
        print('FINISH')
        taxonomy.additional_data = {
            'taxonID': row['TAXON_ID']
        }
        taxonomy.save()
        if self.module_group:
            self.module_group.taxonomies.add(taxonomy)

    def __init__(self, species_data, module_group = None):
        if module_group:
            self.module_group = module_group
        for species_single_data in species_data:
            self.process_data(species_single_data)


class OccurrenceDarwinCore(OccurrenceProcessor):
    fetch_location_context = False
    def handle_error(self, row, message):
        print(f'ERROR - {message}')

    def create_history_data(self, row, record):
        try:
            ingested_data_values = {
                'content_type': ContentType.objects.get_for_model(
                    BiologicalCollectionRecord
                ),
                'data_key': row['ALL_DATA']['eventID'],
                'category': 'Odonata'
            }
            ingested_data = (
                IngestedData.objects.filter(
                    **ingested_data_values
                )
            )
            if not ingested_data.exists():
                IngestedData.objects.create(
                    object_id=record.id,
                    **ingested_data_values
                )
            else:
                ingested_data.update(
                    object_id=record.id
                )
        except KeyError:
            pass

    def finish_processing_row(self, row, record):
        print(f'FINISH - {row}')
        record.additional_data = row['ALL_DATA']
        record.save()
        self.create_history_data(row, record)

    def __init__(self, occurrence_data, module_group):
        self.module_group = module_group
        self.start_process()
        for occurrence in occurrence_data:
            try:
                if IngestedData.objects.filter(
                    data_key=occurrence['ALL_DATA']['eventID'],
                    is_valid=False
                ).exists():
                    print(f'{occurrence["ALL_DATA"]["eventID"]} '
                          f'already exist in the system, and it\'s not valid')
                    continue
            except KeyError:
                print(f'MISSING eventID - Skip')
                continue
            print(f'Processing {occurrence}')
            self.process_data(occurrence)
            print(f'-----------------------')
        self.finish_process()


class Command(BaseCommand):
    """
    Read darwin core data then convert and store them as bims data
    """
    api_token = ''
    source_name = (
        'OdonataMap Virtual Museum, '
        'FitzPatrick Institute of African Ornithology, '
        'University of Cape Town'
    )
    source_year = '2021'
    notes = (
        'Data extracted from the Odonata VM database, 28 Sep 2020'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '-token',
            '--token',
            dest='token',
            default='',
            help='Api token for the request'
        )
        parser.add_argument(
            '-is',
            '--import-species',
            dest='import_species',
            default='False',
            help='Whether to import species or not'
        )
        parser.add_argument(
            '-io',
            '--import-occurrences',
            dest='import_occurrences',
            default='False',
            help='Whether to import occurrences or not'
        )
        parser.add_argument(
            '-sn',
            '--source-name',
            dest='source_name',
            default=self.source_name,
            help='Source name'
        )
        parser.add_argument(
            '-sy',
            '--source-year',
            dest='source_year',
            default=self.source_year,
            help='Source year'
        )
        parser.add_argument(
            '-nt',
            '--notes',
            dest='notes',
            default=self.notes,
            help='Notes'
        )
        parser.add_argument(
            '-s',
            '--start-index',
            dest='start_index',
            default=0,
            help='An index of the first entity to retrieve'
        )
        parser.add_argument(
            '-l',
            '--limit',
            dest='limit',
            default=10,
            help='How many data should be retrieved'
        )

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

    def download_csv_data(self, start_index=0, limit=10):
        """
        Download csv data from odonata server
        :return name of the zipped odonata data
        """
        url = (
            f'http://api.adu.org.za/vmus/v2/dwc/OdonataMAP/'
            f'{self.api_token}/all/json/{start_index},{limit}'
        )
        r = requests.get(url, allow_redirects=True)
        odonata_folder = os.path.join(
            settings.MEDIA_ROOT, 'Odonata'
        )
        if not os.path.exists(odonata_folder):
            os.mkdir(odonata_folder)
        csv_file = os.path.join(
            odonata_folder,
            'Odonata.csv'
        )
        with open(csv_file, 'w') as data_file:
            csv_writer = csv.writer(data_file)
            count = 0
            content_data = json.loads(r.content)
            for data in content_data['data']['result']:
                if count == 0:
                    header = data.keys()
                    csv_writer.writerow(header)
                    count += 1
                csv_writer.writerow(
                    list(map(lambda s: s.strip().replace('\n', '').replace('\r', '') if s else '', data.values())))

        # Zip the file
        zip_name = (time.ctime() + f' - Data: {start_index}-{limit}.zip').replace(' ', '_')
        zip_file = os.path.join(odonata_folder, zip_name)
        with zipfile.ZipFile(zip_file, 'w', zipfile.ZIP_DEFLATED) as zf:
            zf.write(csv_file, 'Odonata.csv')

        os.remove(csv_file)
        return zip_file

    def handle(self, *args, **options):
        self.api_token = options.get('token', '')
        if not self.api_token:
            print('Missing API TOKEN')
            return
        start_index = options.get('start_index', 0)
        limit = options.get('limit', 10)
        source_year = options.get('source_year')
        source_name = options.get('source_name')
        notes = options.get('notes')
        import_species = ast.literal_eval(options.get('import_species'))
        import_occurrences = ast.literal_eval(
            options.get('import_occurrences')
        )
        odonata_zip_file = self.download_csv_data(start_index, limit)
        index = 1
        with DwCAReader(odonata_zip_file) as dwca:
            bims_occurrence_data = []
            bims_species_data = []
            stored_taxon_id = []
            for row in dwca:
                try:
                    month = row.data['month']
                    day = row.data['day']
                    if month == '0':
                        month = '01'
                    if day == '0':
                        day = '01'

                    index += 1
                    taxon_rank = row.data['taxonRank']
                    if taxon_rank == 'species':
                        species_name = '{genus} {spc}'.format(
                            genus=row.data['genus'],
                            spc=row.data['specificEpithet']
                        )
                    else:
                        if 'sub' in taxon_rank:
                            taxon_rank = taxon_rank.replace('sub', '')
                        species_name = row.data[taxon_rank]
                    if row.data['taxonID'] not in stored_taxon_id:
                        stored_taxon_id.append(row.data['taxonID'])
                        cons_status = row.data['dynamicProperties']
                        if cons_status:
                            cons_status = cons_status.split(' ')
                            cons_status = cons_status[0]
                        bims_species_data.append({
                            KINGDOM: row.data['kingdom'],
                            PHYLUM: row.data['phylum'],
                            CLASS: row.data['class'],
                            ORDER: row.data['order'],
                            FAMILY: row.data['family'],
                            GENUS: row.data['genus'],
                            SCIENTIFIC_NAME: (
                                f'{row.data["scientificName"]} '
                                f'{row.data["scientificNameAuthorship"]}'),
                            COMMON_NAME: row.data['vernacularName'],
                            CONSERVATION_STATUS: cons_status,
                            TAXON_RANK: row.data['taxonRank'],
                            TAXON: species_name,
                            TAXON_ID: row.data['taxonID']
                        })

                    bims_occurrence_data.append({
                        SAMPLING_METHOD: row.data['basisOfRecord'],
                        COLLECTOR_OR_OWNER: f'{row.data["datasetName"]} VM',
                        CUSTODIAN: row.data['institutionCode'],
                        DOCUMENT_AUTHOR: row.data['recordedBy'],
                        SITE_DESCRIPTION: row.data['locality'],
                        LATITUDE: row.data['decimalLatitude'],
                        LONGITUDE: row.data['decimalLongitude'],
                        SOURCE: source_name,
                        SOURCE_YEAR: source_year,
                        SAMPLING_DATE: (
                            f'{row.data["year"]}/'
                            f'{month}/'
                            f'{day}'),
                        REFERENCE: row.data['datasetName'],
                        REFERENCE_CATEGORY: 'database',
                        SPECIES_NAME: species_name,
                        'Taxon rank': row.data['taxonRank'],
                        UUID: str(
                            uuid.uuid5(
                                uuid.NAMESPACE_DNS, row.data['occurrenceID'])),
                        NOTES: notes,
                        ALL_DATA: row.data
                    })
                except Exception as e:
                    print(e)

            module_group, _ = TaxonGroup.objects.get_or_create(
                name='Odonate Adults',
                category=TaxonomicGroupCategory.SPECIES_MODULE.name,
            )

            if import_species:
                TaxaDarwinCore(bims_species_data, module_group)

            if import_occurrences:
                OccurrenceDarwinCore(bims_occurrence_data, module_group)
