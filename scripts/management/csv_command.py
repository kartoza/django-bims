import os
import csv
from django.core.management import BaseCommand
from django.conf import settings
from bims.utils.logger import log


class CsvCommand(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument(
            '-file',
            '--csv-file',
            dest='csv_file',
            default=None,
            help='CSV file for updating sites data'
        )

    def handle(self, *args, **options):
        csv_file_name = options.get('csv_file', None)
        csv_file_path = os.path.join(
            settings.MEDIA_ROOT,
            csv_file_name
        )
        if not csv_file_name or not os.path.exists(csv_file_path):
            log('Csv file name not provided / csv file does not exist')
            return False

        with open(csv_file_path) as csv_file:
            self.csv_dict_reader(csv.DictReader(csv_file))

    def csv_dict_reader(self, csv_reader):
        # Read csv file
        raise NotImplementedError
