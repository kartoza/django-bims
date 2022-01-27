import csv
import logging
import os

from django.db.models.fields.reverse_related import ForeignObjectRel

from bims.models.biological_collection_record import BiologicalCollectionRecord
from django.core.management.base import BaseCommand
from django.db.models import Q

from bims.helpers.get_duplicates import get_duplicate_records
from bims.serializers.bio_collection_serializer import \
    BioCollectionOneRowSerializer

logger = logging.getLogger('bims')

data_directory = os.path.join(
    os.path.dirname(os.path.realpath(__file__)), 'data')


class Command(BaseCommand):
    help = 'Fix duplicate records'

    def merge_duplicate_records(self, duplicate_records):
        for record in duplicate_records:
            survey_date = record['survey__date']
            col_date = record['collection_date']
            if isinstance(survey_date, str):
                if 'T' in survey_date:
                    survey_date = survey_date.split('T')[0]
            else:
                survey_date = str(survey_date)
            if isinstance(col_date, str):
                if 'T' in col_date:
                    col_date = col_date.split('T')[0]
            else:
                col_date = str(col_date)
            query = Q(Q(site_id=record['site_id']) &
                      Q(biotope_id=record['biotope_id']) &
                      Q(specific_biotope_id=record[
                          'specific_biotope_id']) &
                      Q(substratum_id=record['substratum_id']) &
                      Q(taxonomy_id=record['taxonomy_id']) &
                      Q(survey__date=survey_date) &
                      Q(collection_date=col_date) &
                      Q(abundance_number=record['abundance_number']))
            records = BiologicalCollectionRecord.objects.filter(
                query
            )
            record_to_keep = records[0]
            records_to_delete = records.exclude(id=record_to_keep.id)

            links = [
                rel.get_accessor_name() for rel in
                record_to_keep._meta.get_fields() if
                issubclass(type(rel), ForeignObjectRel)
            ]
            if links:
                for record_delete in records_to_delete:
                    logger.info('----- {} -----'.format(str(record_delete)))
                    for link in links:
                        try:
                            objects = getattr(record_delete, link).all()
                            if objects.count() > 0:
                                logger.info(
                                    f'Updating '
                                    f'{str(objects.model._meta.label)} '
                                    f'for : {str(record_delete)}')
                                update_dict = {
                                    getattr(record_delete,
                                            link).field.name: record_delete
                                }
                                objects.update(**update_dict)
                        except Exception as e:  # noqa
                            continue

            records_to_delete.delete()

    def handle(self, *args, **options):
        duplicate = get_duplicate_records()

        logger.info(
            'Total duplicate records : {}'.format(duplicate.count())
        )


        logger.info('Merge GBIF duplicate records')
        gbif_duplicate = duplicate.filter(
            source_collection='gbif'
        )
        logger.info(
            f'Total gbif duplicate records : {gbif_duplicate.count()}'
        )
        self.merge_duplicate_records(gbif_duplicate)


        fbis_duplicate = duplicate.exclude(
            source_collection='gbif')
        fbis_with_import_source = fbis_duplicate.filter(
            additional_data__import_source__isnull=False
        ).exclude(
            notes__exact='from sass'
        )
        fbis_sass = fbis_duplicate.filter(
            notes__iexact='from sass'
        )

        logger.info(
            f'Total fbis duplicate records : {fbis_duplicate.count()}',
        )
        logger.info(
            f'Total fbis with import source: {fbis_with_import_source.count()}',
        )
        logger.info(
            f'Total fbis sass : {fbis_sass.count()}'
        )

        # Remove FBIS with import source
        for record in fbis_with_import_source:
            survey_date = record['survey__date']
            col_date = record['collection_date']
            if isinstance(survey_date, str):
                if 'T' in survey_date:
                    survey_date = survey_date.split('T')[0]
            else:
                survey_date = str(survey_date)
            if isinstance(col_date, str):
                if 'T' in col_date:
                    col_date = col_date.split('T')[0]
            else:
                col_date = str(col_date)
            query = Q(Q(site_id=record['site_id']) &
                      Q(biotope_id=record['biotope_id']) &
                      Q(specific_biotope_id=record[
                          'specific_biotope_id']) &
                      Q(substratum_id=record['substratum_id']) &
                      Q(taxonomy_id=record['taxonomy_id']) &
                      Q(survey__date=survey_date) &
                      Q(collection_date=col_date) &
                      Q(additional_data__import_source__isnull=False) &
                      Q(abundance_number=record['abundance_number']))
            records = BiologicalCollectionRecord.objects.filter(
                query
            )
            logger.info(f'Remove {records.count()} records')
            records.delete()

        remaining = (
            fbis_duplicate.exclude(
                additional_data__import_source__isnull=False).exclude(
                notes__iexact="from sass")
        )

        rows = []
        headers = []

        for record in remaining[0:100]:
            survey_date = record['survey__date']
            if isinstance(survey_date, str):
                if 'T' in survey_date:
                    survey_date = survey_date.split('T')[0]
            else:
                survey_date = str(survey_date)
            query = Q(Q(site_id=record['site_id']) &
                      Q(biotope_id=record['biotope_id']) &
                      Q(specific_biotope_id=record['specific_biotope_id']) &
                      Q(substratum_id=record['substratum_id']) &
                      Q(taxonomy_id=record['taxonomy_id']) &
                      Q(survey__date=survey_date) &
                      Q(abundance_number=record['abundance_number']))
            records = BiologicalCollectionRecord.objects.filter(
                query
            )
            serializer = BioCollectionOneRowSerializer(
                records,
                many=True,
                context={'show_link': True}
            )
            if len(serializer.data[0].keys()) > len(headers):
                headers = serializer.data[0].keys()
            rows += list(serializer.data)
            logger.info(
                f'Total duplicate for {survey_date} : {records.count()}'
            )
        formatted_headers = []
        # Rename headers
        for header in headers:
            if header == 'class_name':
                header = 'class'
            header = header.replace('_or_', '/')
            header = header.replace('_', ' ').capitalize()
            formatted_headers.append(header)
        path_file = os.path.join(data_directory, 'duplicate_records.csv')
        with open(path_file, 'w') as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=formatted_headers)
            writer.writeheader()
            writer.fieldnames = headers
            for row in rows:
                try:
                    writer.writerow(row)
                except ValueError:
                    logger.error(row)
                    pass
