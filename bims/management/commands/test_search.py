# coding=utf-8
__author__ = 'Anita Hapsari <anita@kartoza.com>'
__date__ = '05/06/18'

from django.core.management.base import BaseCommand
from core.documents import BiologicalCollectionRecordDocument


class Command(BaseCommand):
    def handle(self, *args, **options):
        s = BiologicalCollectionRecordDocument.search().query(
            "match", original_species_name="rock-spec")

        for hit in s:
            print(
                "Car name : {}, description {}".format(
                    hit.name, hit.description)
            )
