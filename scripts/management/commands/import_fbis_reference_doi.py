# -*- coding: utf-8 -*-
import os
import csv
import uuid
from datetime import datetime
from requests.exceptions import HTTPError
from django.core.management.base import BaseCommand
from django.contrib.gis.geos import Point

from bims.utils.logger import log
from bims.models import (
    BiologicalCollectionRecord,
    LocationSite,
    SourceReference
)
from td_biblio.exceptions import DOILoaderError
from td_biblio.models.bibliography import Entry
from td_biblio.utils.loaders import DOILoader


LATITUDE = 'Latitude'
LONGITUDE = 'Longitude'
DOI = 'DOI'
REFERENCE = 'Reference'
REFERENCE_CATEGORY = 'Reference category'
UUID = 'UUID'
LOCATION_SITE = 'River'
SPECIES_NAME = 'Taxon'
ORIGIN = 'Origin'
COLLECTOR = 'Collector/Assessor'
SAMPLING_DATE = 'Sampling Date'


class Command(BaseCommand):
    """Import fish data from file"""
    file_name = 'fbis_data_with_references.csv'

    def handle(self, *args, **options):
        folder_name = 'data'

        file_path = os.path.join(
            os.path.abspath(os.path.dirname(__name__)),
            'scripts/static/{folder}/{filename}'.format(
                folder=folder_name,
                filename=self.file_name
            ))

        found = 0
        not_found = 0
        data_error = 0


        with open(file_path, 'r') as csvfile:
            csv_reader = csv.DictReader(csvfile)
            for index, record in enumerate(csv_reader):
                try:
                    record_point = Point(
                        float(record[LONGITUDE]),
                        float(record[LATITUDE]))

                    location_sites = LocationSite.objects.filter(
                        geometry_point=record_point,
                        name=record[LOCATION_SITE]
                    )

                    if not location_sites.exists():
                        log('no location site')
                        continue
                    else:
                        location_site = location_sites[0]

                    if record[SAMPLING_DATE].lower() == 'unspecified':
                        log('Unspecified date -> Next row')
                        continue
                    uuid_value = uuid.UUID(record[UUID])
                    collection_records = (
                        BiologicalCollectionRecord.objects.filter(
                            uuid=uuid_value
                        )
                    )
                    if not collection_records.exists():
                        if record[ORIGIN] == 'Native':
                            category = 'indigenous'
                        else:
                            category = 'alien'
                        collection_records = (
                            BiologicalCollectionRecord.objects.filter(
                                site=location_site,
                                original_species_name=record[
                                    SPECIES_NAME
                                ],
                                collection_date=datetime.strptime(
                                    record[SAMPLING_DATE], '%Y/%m/%d'),
                                category=category,
                                collector=record[COLLECTOR],
                                notes=record['Notes']
                            )
                        )
                    if collection_records.count() != 1:
                        print('multiple collection records or zero')
                        not_found += 1
                        continue

                    print('found collection record %s' % collection_records[0].id)
                    found += 1
                    collection_record = collection_records[0]
                    collection_record.uuid = str(uuid_value)
                    collection_record.save()
                    # log('Processing : %s' % record[REFERENCE])
                    # doi = record[DOI]
                    # if not doi:
                    #     log('DOI not found, skipping')
                    #     continue
                    # else:
                    #     doi = doi.strip()
                    # collection_records = (
                    #     BiologicalCollectionRecord.objects.filter(
                    #         reference=record[REFERENCE],
                    #         source_reference__isnull=True
                    #     )
                    # )
                    # if not collection_records:
                    #     log('Collection records not found, skipping')
                    #     continue
                    #
                    # # Add doi
                    # try:
                    #     entry = Entry.objects.get(doi__iexact=doi)
                    # except Entry.DoesNotExist:
                    #     doi_loader = DOILoader()
                    #
                    #     try:
                    #         doi_loader.load_records(DOIs=[doi])
                    #     except DOILoaderError as e:
                    #         log('DOILoaderError, skipping')
                    #         continue
                    #     except HTTPError:
                    #         log('Could not fetch the doi, skipping')
                    #         continue
                    #
                    #     doi_loader.save_records()
                    #
                    #     try:
                    #         entry = Entry.objects.get(doi__iexact=doi)
                    #     except Entry.DoesNotExist:
                    #         log('Entry does not exist, skipping')
                    #         continue
                    #
                    # source_reference = (
                    #     SourceReference.create_source_reference(
                    #         category='bibliography',
                    #         source_id=entry.id,
                    #         note=None
                    #     )
                    # )
                    #
                    # collection_records.update(
                    #     source_reference=source_reference
                    # )

                except KeyError as e:
                    log('KeyError', index)
                    data_error += 1
                    continue
                except ValueError as e:
                    log('ValueError', index)
                    data_error += 1
                    continue

            log('Summary')
            log('Total found : %s' % found)
            log('Total not found: %s' % not_found)
            log('Total data error: %s' % data_error)
