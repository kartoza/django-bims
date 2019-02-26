# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand
from bims.scripts.import_fish_species_from_file import *


class Command(BaseCommand):
    help = 'Fetch all species from gbif'

    def handle(self, *args, **options):
        import_fish_species_from_file()
