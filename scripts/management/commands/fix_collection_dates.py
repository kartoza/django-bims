import logging
from django.core.management.base import BaseCommand
from bims.models import BiologicalCollectionRecord, Survey
from django.db.models import F
from django.db import transaction, connection

from bims.signals.utils import disconnect_bims_signals, connect_bims_signals

logger = logging.getLogger(__name__)

BATCH_SIZE = 100


class Command(BaseCommand):
    help = 'Ensure BiologicalCollectionRecord collection_date matches Survey date'

    def add_arguments(self, parser):
        parser.add_argument(
            '-s',
            '--schema-name',
            dest='schema_name',
            default='public',
            help='Schema name to use for the database connection.'
        )

    def handle(self, *args, **options):
        schema_name = options.get('schema_name', '')
        if schema_name:
            connection.set_schema(schema_name)
        disconnect_bims_signals()
        self.fix_collection_dates(schema_name)
        connect_bims_signals()

    def fix_collection_dates(self, schema_name):
        mismatched_records = BiologicalCollectionRecord.objects.exclude(
            collection_date=F('survey__date')
        )

        record_count = mismatched_records.count()
        logger.info(f'Found {record_count} records with mismatched dates')

        if schema_name:
            connection.set_schema(schema_name)

        record_count = mismatched_records.count()
        logger.info(f'Found {record_count} records with mismatched dates')

        if record_count == 0:
            return

        for start in range(0, record_count, BATCH_SIZE):
            with transaction.atomic():
                batch = mismatched_records[start:start + BATCH_SIZE]
                self.process_batch(batch)
            print('next batch')

    def process_batch(self, batch):
        for record in batch.iterator():
            logger.info(f'Fixing record ID {record.id}')

            survey = self.get_or_create_survey(record)

            record.survey = survey
            record.save()
            logger.info(f'Updated record ID {record.id} to survey ID {survey.id}')

    def get_or_create_survey(self, record):
        surveys = Survey.objects.filter(
            date=record.collection_date,
            site=record.survey.site
        )

        if surveys.exists():
            survey = surveys.first()
            if surveys.count() > 1:
                logger.warning(
                    f'Multiple surveys found for site {record.survey.site.id} on '
                    f'{record.collection_date}. Using survey ID {survey.id}.')
        else:
            survey = Survey.objects.create(
                date=record.collection_date,
                site=record.survey.site,
                collector_string=record.survey.collector_string,
                uuid=record.survey.uuid,
                mobile=record.survey.mobile,
            )
            logger.info(f'Created new survey with ID {survey.id}')

        return survey
