# -*- coding: utf-8 -*-
import os
import csv
from requests.exceptions import HTTPError
from django.core.management.base import BaseCommand

from bims.utils.logger import log
from bims.models import (
    BiologicalCollectionRecord,
    SourceReference
)
from td_biblio.exceptions import DOILoaderError
from td_biblio.models.bibliography import Entry
from td_biblio.utils.loaders import DOILoader


DOI = 'DOI'
REFERENCE = 'Reference'
REFERENCE_CATEGORY = 'Reference category'


class Command(BaseCommand):
    """Import fish data from file"""
    file_name = 'fbis_reference_doi.csv'

    def handle(self, *args, **options):
        folder_name = 'data'

        file_path = os.path.join(
            os.path.abspath(os.path.dirname(__name__)),
            'bims/static/{folder}/{filename}'.format(
                folder=folder_name,
                filename=self.file_name
            ))

        with open(file_path, 'r') as csvfile:
            csv_reader = csv.DictReader(csvfile)
            for index, record in enumerate(csv_reader):
                try:
                    log('Processing : %s' % record[REFERENCE])
                    doi = record[DOI]
                    if not doi:
                        log('DOI not found, skipping')
                        continue
                    else:
                        doi = doi.strip()
                    collection_records = (
                        BiologicalCollectionRecord.objects.filter(
                            reference=record[REFERENCE],
                            source_reference__isnull=True
                        )
                    )
                    if not collection_records:
                        log('Collection records not found, skipping')
                        continue

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

                    collection_records.update(
                        source_reference=source_reference
                    )

                except KeyError as e:
                    log('KeyError : {}'.format(e.message), index)
                    continue
                except ValueError as e:
                    log('ValueError : {}'.format(e.message), index)
                    continue
