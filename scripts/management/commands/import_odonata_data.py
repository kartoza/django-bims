import logging
from django.core.management import BaseCommand
from django.contrib.contenttypes.models import ContentType

from bims.scripts.collection_csv_keys import *  # noqa
from bims.scripts.species_keys import *  # noqa
from bims.scripts.taxa_upload import TaxaProcessor
from bims.models.biological_collection_record import BiologicalCollectionRecord
from bims.scripts.occurrences_upload import OccurrenceProcessor
from bims.models.ingested_data import IngestedData
from bims.utils.user import get_user_reverse
from scripts.virtual_museum import VirtualMuseumHarvester

logger = logging.getLogger('bims')

ALL_DATA = 'ALL_DATA'
TAXON_ID = 'TAXON_ID'
COLLECTOR_ONLY = 'Collector'


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
    module_name = 'Odonata'
    base_api_url = 'http://api.adu.org.za/vmus/v2/dwc/OdonataMAP/'

    def add_arguments(self, parser):
        parser.add_argument(
            '-token',
            '--token',
            dest='token',
            default='',
            help='Api token for the request'
        )
        parser.add_argument(
            '-sn',
            '--source-name',
            dest='source_name',
            default=self.source_name,
            help='Source name'
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

    def handle(self, *args, **options):
        self.api_token = options.get('token', '')
        if options.get('source_name'):
            self.source_name = options.get('source_name')

        if not self.api_token:
            print('Missing API TOKEN')
            return

        logger.info('Harvesting Odonata data from VM...')
        start_index = options.get('start_index', 0)
        limit = options.get('limit', 10)

        harvester = VirtualMuseumHarvester(
            api_token=self.api_token,
            module_name=self.module_name,
            base_api_url=self.base_api_url,
            source_name=self.source_name,
            taxon_group_module='Odonate Adults')
        harvester.harvest(
            start_index=start_index,
            limit=limit,
            ingest_occurrences=True,
            ingest_species=True
        )
