# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand
from bims.utils.fetch_gbif import fetch_all_species_from_gbif


class Command(BaseCommand):
    help = 'Fetch species from gbif'

    def handle(self, *args, **options):
         fetch_all_species_from_gbif(
             species='Astraspidae',
             taxonomic_rank='family'
         )
