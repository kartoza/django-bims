from django.core.management.base import BaseCommand
from bims.utils.gbif import process_taxon_identifier


class Command(BaseCommand):
    """Update taxa.
    """
    def add_arguments(self, parser):
        parser.add_argument(
            '-k',
            '--key',
            dest='key',
            default=False,
            help='Gbif key')

    def handle(self, *args, **options):
        # Get collection without taxa record
        key = options.get('key')

        if not key:
            print('Need gbif key')
            return

        taxon = process_taxon_identifier(key)

        print('test')
        return
