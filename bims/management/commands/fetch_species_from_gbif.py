# -*- coding: utf-8 -*-
import ast
from django.core.management.base import BaseCommand
from bims.scripts.import_fish_occurrences_from_gbif import (
    import_fish_occurrences_from_gbif
)


class Command(BaseCommand):
    help = 'Fetch all species from gbif'

    def add_arguments(self, parser):
        parser.add_argument(
            '-i',
            '--import-occurrences',
            dest='import_occurrences',
            default=False,
            help='Should also import occurrences from gbif')

        parser.add_argument(
            '-o',
            '--update-origin',
            dest='update_origin',
            default=False,
            help='Update collection origin')

    def handle(self, *args, **options):
        try:
            import_occurrences = (
                ast.literal_eval(options.get('import_occurrences'))
            )
        except ValueError:
            import_occurrences = False
        try:
            update_origin = (
                ast.literal_eval(options.get('update_origin'))
            )
        except ValueError:
            update_origin = False

        import_fish_occurrences_from_gbif(import_occurrences, update_origin)
