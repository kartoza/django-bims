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
    SourceReference,
    DatabaseRecord,
    SourceReferenceBibliography,
    BimsDocument
)
from geonode.documents.models import Document
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
        not_found = []
        data_error = []

        with open(file_path, 'r') as csvfile:
            csv_reader = csv.DictReader(csvfile)
            for index, record in enumerate(csv_reader):
                collection_records = BiologicalCollectionRecord.objects.none()
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
                        if collection_records.count() == 0:
                            not_found.append(-99)
                        else:
                            not_found.extend(
                                list(
                                    collection_records.values_list(
                                        'id', flat=True)))
                        continue

                    print(
                            'found collection record %s' %
                            collection_records[0].id)
                    found += 1
                    collection_record = collection_records[0]
                    collection_record.uuid = str(uuid_value)
                    collection_record.save()

                    reference_category = record['Reference category']
                    document = None
                    document_link = record['Document Upload Link']
                    document_id = document_link.split('/')[
                        len(document_link.split('/'))-1
                    ]
                    if document_id:
                        document_id = int(document_id)
                        try:
                            document = Document.objects.get(
                                id=document_id
                            )
                            bims_document, b_created = (
                                BimsDocument.objects.get_or_create(
                                    document=document
                            ))
                            author = record['Reference']
                            if (
                                    bims_document.author and
                                    bims_document.author != author
                            ):
                                bims_document.author = author
                                bims_document.save()
                        except Document.DoesNotExist:
                            pass
                    if (
                            reference_category ==
                            'Peer-reviewed scientific article'):
                        # peer-reviewed
                        doi = record[DOI].strip()
                        if not doi and not document:
                            continue
                        if doi:
                            # Add doi
                            try:
                                entry = Entry.objects.get(doi__iexact=doi)
                            except Entry.DoesNotExist:
                                doi_loader = DOILoader()
                                try:
                                    doi_loader.load_records(DOIs=[doi])
                                except DOILoaderError as e:
                                    log('DOILoaderError, skipping')
                                    continue
                                except HTTPError:
                                    log('Could not fetch the doi, skipping')
                                    continue
                                doi_loader.save_records()
                                try:
                                    entry = Entry.objects.get(doi__iexact=doi)
                                except Entry.DoesNotExist:
                                    log('Entry does not exist, skipping')
                                    continue
                            source_reference = (
                                SourceReference.create_source_reference(
                                    category='bibliography',
                                    source_id=entry.id,
                                    note=None
                                )
                            )
                            print('Add DOI to %s' % collection_record.id)
                            collection_record.source_reference = (
                                source_reference
                            )
                            collection_record.save()
                        else:
                            source_reference, sr_created = (
                                SourceReferenceBibliography.objects.
                                    get_or_create(
                                    document=document
                                )
                            )
                            collection_record.source_reference = (
                                source_reference
                            )
                            collection_record.save()
                            print('Add Bibliography Document to %s'
                                  % collection_record.id)
                    elif reference_category == 'Database':
                        # Database
                        if not document:
                            continue
                        database_name = record['Reference']
                        database, created = (
                            DatabaseRecord.objects.get_or_create(
                                name=database_name,))
                        source_reference = (
                            SourceReference.create_source_reference(
                                category='database',
                                source_id=database.id,
                                note=None
                            )
                        )
                        source_reference.document = document
                        source_reference.save()
                        collection_record.source_reference = source_reference
                        collection_record.save()

                        print('Add Database Document to %s' %
                              collection_record.id)
                    elif (
                            reference_category == 'Thesis' or
                            reference_category == 'Published report'):
                        # published
                        if not document:
                            continue
                        source_reference = (
                            SourceReference.create_source_reference(
                                category='document',
                                source_id=document.id,
                                note=None
                            )
                        )
                        collection_record.source_reference = source_reference
                        collection_record.save()
                        print('Add Published Document to %s'
                              % collection_record.id)
                    else:
                        # unpublished
                        source_reference, created = (
                            SourceReference.objects.get_or_create(
                                note=record['Reference']
                            ))
                        collection_record.source_reference = source_reference
                        collection_record.save()
                        print('Add Unpublished to %s'
                              % collection_record.id)

                except KeyError as e:
                    print('KeyError')
                    data_error.extend(
                        list(collection_records.values_list('id', flat=True)))
                    continue
                except ValueError as e:
                    print('ValueError')
                    data_error.extend(
                        list(collection_records.values_list('id', flat=True)))
                    continue

            log('Summary')
            log('Total found : %s' % found)
            log('Total not found: %s' % len(not_found))
            log('Total data error: %s' % len(data_error))
