# coding=utf-8
__author__ = 'Anita Hapsari <anita@kartoza.com>'
__date__ = '05/06/18'

from django.core.management.base import BaseCommand
from bims.documents import BiologicalCollectionRecordDocument


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
        s = BiologicalCollectionRecordDocument.search().query(
            "match", original_species_name=options['name'])

        if s.count() > 0:
            for hit in s:
                print(
                    "Object name : {}"
                    "\ncollection_date: {}\n"
                    "collector: {}\n".format(
                        hit.original_species_name,
                        hit.collection_date,
                        hit.collector,
                    )
                )
        else:
            print(
                'No object with original species name: {} is found'.format(
                    options['name']))