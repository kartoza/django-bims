import ast
import csv
import json
import logging
import os
import uuid
import zipfile
from datetime import datetime

import requests
from preferences import preferences

from bims.enums.taxonomic_group_category import TaxonomicGroupCategory

from bims.models.taxon_group import TaxonGroup

from bims.models.ingested_data import IngestedData

from bims.models.biological_collection_record import BiologicalCollectionRecord
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from dwca.read import DwCAReader

from bims.scripts.collection_csv_keys import *  # noqa
from bims.scripts.occurrences_upload import OccurrenceProcessor
from bims.scripts.species_keys import *  # noqa
from bims.scripts.taxa_upload import TaxaProcessor
from bims.utils.get_key import get_key
from bims.utils.user import get_user_reverse

logger = logging.getLogger('bims')

ALL_DATA = 'ALL_DATA'
TAXON_ID = 'TAXON_ID'
COLLECTOR_ONLY = 'Collector'

class TaxaDarwinCore(TaxaProcessor):

    def handle_error(self, row, message):
        logger.info(f'ERROR : {message}')

    def finish_processing_row(self, row, taxonomy):
        logger.info('FINISH')
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
        logger.info(f'ERROR - {message}')

    def create_history_data(self, row, record):
        try:
            ingested_data_values = {
                'content_type': ContentType.objects.get_for_model(
                    BiologicalCollectionRecord
                ),
                'data_key': row['ALL_DATA']['eventID'],
                'category': 'Frog'
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
        logger.info(f'FINISH - {row}')
        record.additional_data = row['ALL_DATA']
        record.source_collection = 'virtual_museum'
        if row[COLLECTOR_ONLY]:
            collector = get_user_reverse(row[COLLECTOR_ONLY])
            record.collector_user = collector
            record.survey.collector_user = collector
            record.survey.save()
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
                    logger.info(f'{occurrence["ALL_DATA"]["eventID"]} '
                                f'already exists, skipping...')
                    continue
            except KeyError:
                logger.info(f'MISSING eventID - Skip')
                continue

            boundary_key = preferences.SiteSetting.boundary_key
            if boundary_key:
                url = (
                    '{base_url}/api/v2/query?registry=service&key={key}&'
                    'x={lon}&y={lat}&outformat=json'
                ).format(
                    base_url=get_key('GEOCONTEXT_URL'),
                    key=boundary_key,
                    lon=occurrence[LONGITUDE],
                    lat=occurrence[LATITUDE]
                )
                try:
                    response = requests.get(url)
                    if response.status_code != 200:
                        logger.info(
                            f'The site is not within a valid border.'
                        )
                        continue
                    else:
                        response_json = json.loads(response.content)
                        if response_json['value']:
                            logger.info(
                                f"Site is in {response_json['value']}"
                            )
                        else:
                            logger.info(
                                f'The site is not within a valid border.'
                            )
                            continue
                except Exception as e:  # noqa
                    logger.info(
                        f'Unable to check boundary data from geocontext')

            logger.info(f'Processing {occurrence}')
            self.process_data(occurrence)
            logger.info(f'-----------------------')
        self.finish_process()


class VirtualMuseumHarvester(object):
    """
    Harvest virtual museum data from virtual museum
    """
    api_token = ''
    module_name = ''
    base_api_url = ''

    source_name = ''
    source_year = ''
    notes = ''
    file_date = ''
    taxon_group_module = ''

    def __init__(self, **kwargs):
        super(VirtualMuseumHarvester, self).__init__()
        date_now = datetime.now()

        self.api_token = kwargs.get('api_token', '')
        self.source_name = kwargs.get('source_name', '')
        self.taxon_group_module = kwargs.get('taxon_group_module', '')
        self.base_api_url = kwargs.get('base_api_url', '')
        self.module_name = kwargs.get('module_name')

        self.file_date = '{date}-{month}-{year}'.format(
            date=date_now.day,
            month=date_now.month,
            year=date_now.year
        )
        self.source_year = str(date_now.year)
        self.notes = (
            'Date extracted from {0} VM database : {1}'.format(
                self.module_name,
                self.file_date
            )
        )

    def download_csv_data(self, start_index: int = 0, limit: int = 10):
        """
        Download csv data from virtual museum
        :return name of the zipped data
        """
        zip_name = (
            f'{self.file_date} - {self.module_name}Data: '
            f'{start_index}-{limit}.zip').replace(' ', '_')

        if os.path.exists(zip_name):
            return zip_name

        url = (
            f'{self.base_api_url}'
            f'{self.api_token}/all/json/{start_index},{limit}'
        )
        r = requests.get(url, allow_redirects=True)
        vm_folder = os.path.join(
            settings.MEDIA_ROOT, 'VirtualMuseum'
        )
        if not os.path.exists(vm_folder):
            os.mkdir(vm_folder)
        csv_file = os.path.join(
            vm_folder,
            '{}.csv'.format(self.module_name)
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
                    list(map(
                        lambda s: s.strip().replace(
                            '\n', '').replace('\r', '') if s else '',
                        data.values())))

        # Zip the file
        zip_file = os.path.join(vm_folder, zip_name)
        with zipfile.ZipFile(zip_file, 'w', zipfile.ZIP_DEFLATED) as zf:
            zf.write(csv_file, '{}.csv'.format(self.module_name))

        os.remove(csv_file)
        return zip_file

    def parse_vm_data(self, zip_file_path: str) -> ([], []):
        """
        Parse zipped vm data then return a tuple of
        (array of occurrences, array of species)
        """
        bims_occurrence_data = []
        bims_species_data = []
        with DwCAReader(zip_file_path) as dwca:
            stored_taxon_id = []
            for row in dwca:
                try:
                    month = row.data['month']
                    day = row.data['day']
                    if month == '0':
                        month = '01'
                    if day == '0':
                        day = '01'

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
                        COLLECTOR_ONLY: row.data['recordedBy'],
                        CUSTODIAN: row.data['institutionCode'],
                        DOCUMENT_AUTHOR: row.data['recordedBy'],
                        SITE_DESCRIPTION: row.data['locality'],
                        LATITUDE: row.data['decimalLatitude'],
                        LONGITUDE: row.data['decimalLongitude'],
                        SOURCE: self.source_name,
                        SOURCE_YEAR: self.source_year,
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
                        NOTES: self.notes,
                        ALL_DATA: row.data
                    })
                except Exception as e:
                    logger.info(e)
        return bims_occurrence_data, bims_species_data


    def harvest(self, start_index: int = 0, limit: int = 0,
                ingest_species: bool = False,
                ingest_occurrences: bool = False):
        """
        Start the harvest process
        :param start_index: start index of virtual museum data
        :param limit: how many data to fetch
        :param ingest_species: fetch and ingest species data
        :param ingest_occurrences: fetch and ingest occurrences data
        """
        zip_file = self.download_csv_data(start_index, limit)
        occurrences, species = self.parse_vm_data(zip_file)

        logger.info(f'Total downloaded occurrences : '
                    f'{len(occurrences)}')

        logger.info(f'Total downloaded species : '
                    f'{len(species)}')

        if not self.taxon_group_module:
            logger.info(f'Missing taxon group module. Closing...')

        module_group, _ = TaxonGroup.objects.get_or_create(
            name=self.taxon_group_module,
            category=TaxonomicGroupCategory.SPECIES_MODULE.name,
        )

        if ingest_species:
            TaxaDarwinCore(species, module_group)

        if ingest_occurrences:
            OccurrenceDarwinCore(occurrences, module_group)
