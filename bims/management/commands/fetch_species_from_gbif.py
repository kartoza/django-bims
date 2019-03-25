# -*- coding: utf-8 -*-
import ast
from django.core.management.base import BaseCommand
from bims.scripts.import_fish_species_from_file import (
    import_fish_species_from_file
)


class Command(BaseCommand):
    help = 'Fetch all species from gbif'

    def add_arguments(self, parser):
        parser.add_argument(
            '-i',
            '--import-occurrences',
            dest='import_occurrences',
            default=True,
            help='Should also import occurrences from gbif')

    def handle(self, *args, **options):
        try:
            import_occurrences = (
                ast.literal_eval(options.get('import_occurrences'))
            )
        except ValueError:
            import_occurrences = False

        import_fish_species_from_file(import_occurrences)
