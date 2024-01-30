import logging
from django.core.management import BaseCommand

from bims.scripts.collection_csv_keys import *  # noqa
from bims.scripts.species_keys import *  # noqa
from scripts.virtual_museum import VirtualMuseumHarvester

logger = logging.getLogger('bims')


class Command(BaseCommand):
    """
    Harvest Frog data from virtual museum
    """
    api_token = ''
    module_name = 'Frog'
    base_api_url = 'https://api.birdmap.africa/vmus/v2/dwc/FrogMAP/'

    source_name = (
        'FrogMap Virtual Museum Database'
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
        parser.add_argument(
            '-sn',
            '--source-name',
            dest='source_name',
            default=self.source_name,
            help='Source name'
        )
        parser.add_argument(
            '-md',
            '--module-name',
            dest='module_name',
            default='Anurans',
            help='Module Name'
        )

    def handle(self, *args, **options):
        self.api_token = options.get('token', '')
        if options.get('source_name'):
            self.source_name = options.get('source_name')

        if not self.api_token:
            logger.info('Missing API TOKEN!')
            return

        logger.info('Harvesting FROG data from VM...')
        start_index = options.get('start_index', 0)
        limit = options.get('limit', 10)

        harvester = VirtualMuseumHarvester(
            api_token=self.api_token,
            module_name=self.module_name,
            base_api_url=self.base_api_url,
            source_name=self.source_name,
            taxon_group_module=options.get('module_name'))
        harvester.harvest(
            start_index=start_index,
            limit=limit,
            ingest_occurrences=True
        )
