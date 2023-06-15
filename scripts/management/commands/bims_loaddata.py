from django.core.management.base import BaseCommand, CommandError
from django.core.serializers import deserialize
import json

from bims.models import SiteSetting


class Command(BaseCommand):
    help = 'Loads JSON data and deserializes it into a Django model.'

    def add_arguments(self, parser):
        parser.add_argument(
            'json_file',
            type=str,
            help="The JSON file containing serialized Django model data.")

    def handle(self, *args, **options):
        json_file = options['json_file']

        try:
            with open(json_file, 'r') as f:
                data = json.load(f)
        except FileNotFoundError:
            raise CommandError(f"The file {json_file} does not exist.")

        # The 'deserialize' function expects a string of serialized data,
        # so we need to re-serialize our data into a string.
        data_str = json.dumps(data)
        site_setting = SiteSetting.objects.first()

        for deserialized_object in deserialize('json', data_str):
            deserialized_object.object.id = site_setting.id
            deserialized_object.object.preferences_ptr_id = site_setting.id
            deserialized_object.save()

        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully loaded data from "{json_file}" '
                f'and deserialized it.')
        )
