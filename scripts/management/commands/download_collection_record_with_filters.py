# -*- coding: utf-8 -*-
import os
import csv
from django.db.models import Q
from django.conf import settings
from bims.models import (
    BiologicalCollectionRecord
)
from bims.utils.logger import log
from scripts.management.csv_command import CsvCommand


class Command(CsvCommand):


    def csv_dict_reader(self, csv_reader):
        missing = 0
        bio_ids = []

        log('Searching records based on uuid...')
        for row in csv_reader:
            uuid = row['uuid']
            uuid_without_hyphen = uuid.replace('-', '')
            bio = BiologicalCollectionRecord.objects.filter(
                Q(uuid=uuid) |
                Q(uuid=uuid_without_hyphen)
            )
            if not bio.exists():
                missing += 1
            bio_ids.append(bio.first().id)

        collection_results = BiologicalCollectionRecord.objects.filter(
            id__in=bio_ids
        )

        log('Found {} records'.format(collection_results.count()))
        log('Missing {} records'.format(missing))

        # SRID = Source Reference ID
        # MID = Module Group ID
        headers = ['UUID', 'SRID', 'MID']

        file_name = 'download_collection_record_with_filters_results.csv'
        path_file = os.path.join(
            settings.MEDIA_ROOT,
            file_name
        )
        log('Saving results to {}'.format(file_name))
        with open(path_file, 'w') as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=headers)
            writer.writeheader()
            writer.fieldnames = headers
            for row in collection_results:
                try:
                    writer.writerow({
                        'UUID': row.uuid,
                        'SRID': row.source_reference.id,
                        'MID': row.module_group_id
                    })
                except UnicodeEncodeError:
                    continue
