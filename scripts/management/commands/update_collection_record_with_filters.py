# -*- coding: utf-8 -*-
from django.db.models import Q
from bims.models import (
    BiologicalCollectionRecord, SourceReference, TaxonGroup
)
from bims.utils.logger import log
from scripts.management.csv_command import CsvCommand


class Command(CsvCommand):

    def csv_dict_reader(self, csv_reader):
        missing = 0

        log('Searching records based on uuid...')

        # SRID = Source Reference ID
        # MID = Module Group ID
        headers = ['UUID', 'SRID', 'MID']

        for row in csv_reader:
            uuid = row['UUID']
            uuid_without_hyphen = uuid.replace('-', '')
            bio = BiologicalCollectionRecord.objects.filter(
                Q(uuid=uuid) |
                Q(uuid=uuid_without_hyphen)
            )
            if not bio.exists():
                missing += 1

            bio = bio.first()
            log('Updating {}'.format(bio))
            source_reference = SourceReference.objects.filter(
                id=row['SRID']
            )
            if source_reference.exists():
                bio.source_reference = source_reference.first()

            taxon_module = TaxonGroup.objects.filter(id=row['MID'])
            if taxon_module.exists():
                bio.module_group = taxon_module.first()

            bio.save()
