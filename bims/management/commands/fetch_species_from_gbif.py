# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand
from bims.utils.fetch_gbif import fetch_all_species_from_gbif


class Command(BaseCommand):
    help = 'Fetch all species from gbif'

    def add_arguments(self, parser):
        parser.add_argument(
            '-s',
            '--species',
            dest='species',
            default='',
            help='Species name to fetch')
        parser.add_argument(
            '-r',
            '--rank',
            dest='rank',
            default='',
            help='Taxonomy rank to fetch')

    def handle(self, *args, **options):
        rank = options.get('rank', None)
        species = options.get('species', None)
        fetch_all_species_from_gbif(
            species=species,
            taxonomic_rank=rank
        )
