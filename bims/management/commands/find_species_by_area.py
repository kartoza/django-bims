# -*- coding: utf-8 -*-
from django.core.management import BaseCommand

from bims.utils.gbif import find_species_by_area


class Command(BaseCommand):

    def handle(self, *args, **options):
        species = find_species_by_area(
            boundary_id=99,
            class_key=212)
