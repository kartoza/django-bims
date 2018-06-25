# coding=utf-8
__author__ = 'Anita Hapsari <anita@kartoza.com>'
__date__ = '05/06/18'

from django.core.management.base import BaseCommand
from bims.models.biological_collection_record import \
    BiologicalCollectionRecord
from haystack.query import SearchQuerySet


class Command(BaseCommand):
    """Command to test elasticsearch."""

    def add_arguments(self, parser):
        parser.add_argument(
            '--name',
            dest='name',
            help='original species name',
        )

    def handle(self, *args, **options):
        print('test searching')

        s = SearchQuerySet().filter(
                original_species_name=options['name']
        ).models(BiologicalCollectionRecord)

        print(s.count())

        if s.count() > 0:
            for hit in s:
                print(hit.original_species_name)
        else:
            print(
                'No object with original species name: {} is found'.format(
                    options['name']))
