import logging
from django.core.management.base import BaseCommand
from django.db import transaction, connection
from django.db.models import F

from bims.models import BiologicalCollectionRecord, Survey
from bims.signals.utils import disconnect_bims_signals, connect_bims_signals

logger = logging.getLogger(__name__)

BATCH_SIZE = 1000


class Command(BaseCommand):
    """
    A command to ensure that each BiologicalCollectionRecord's collection_date
    matches its linked Survey's date. If they differ, it will either attach the
    record to an existing Survey with the matching date (and same site)
    or create a new Survey.
    """
    help = 'Ensure BiologicalCollectionRecord.collection_date matches Survey.date'

    def add_arguments(self, parser):
        parser.add_argument(
            '-s',
            '--schema-name',
            dest='schema_name',
            default='public',
            help='Schema name to use for the database connection.'
        )
        parser.add_argument(
            '-d',
            '--dry-run',
            action='store_true',
            dest='dry_run',
            default=False,
            help='Run in simulate (dry-run) mode without making any changes.'
        )

    def handle(self, *args, **options):
        """
        Entry point for the management command. Sets the schema, disconnects
        signals, fixes the collection dates, then reconnects signals.
        """
        schema_name = options.get('schema_name', '')
        dry_run = options.get('dry_run', False)

        if schema_name:
            connection.set_schema(schema_name)

        if dry_run:
            logger.info('Running in DRY-RUN mode. No changes will be committed.')

        disconnect_bims_signals()
        self.fix_collection_dates(dry_run=dry_run)
        connect_bims_signals()

    def fix_collection_dates(self, dry_run=False):
        """
        Continuously fetch batches of records that have mismatched dates,
        and fix them until none remain.
        """
        while True:
            mismatched_batch = BiologicalCollectionRecord.objects.exclude(
                collection_date=F('survey__date')
            )[:BATCH_SIZE]

            # If there are no more mismatches, we're done
            batch_count = mismatched_batch.count()
            if batch_count == 0:
                logger.info('No more mismatched dates found. Exiting...')
                break

            logger.info(f'Found {batch_count} mismatched records in this batch.')

            if not dry_run:
                with transaction.atomic():
                    self.process_batch(mismatched_batch, dry_run=dry_run)
            else:
                self.process_batch(mismatched_batch, dry_run=dry_run)

    def process_batch(self, batch, dry_run=False):
        """
        For each record in the batch, ensure the record's collection_date
        matches its survey date by either using an existing Survey for
        that date or creating a new one.

        If dry_run=True, only log the intended changes without saving.
        """
        for record in batch.iterator():
            # If no survey is attached at all, log and skip
            if not record.survey:
                logger.warning(
                    f'Record ID {record.id} has no associated survey; skipping.'
                )
                continue

            if record.collection_date == record.survey.date:
                # Already correct; skip
                continue

            logger.info(
                f'Mismatch for record ID {record.id}: Survey date '
                f'{record.survey.date} != Collection date {record.collection_date}'
            )

            if dry_run:
                logger.info(
                    f'[DRY-RUN] Would update record ID {record.id} '
                    f'from {record.survey.date} to {record.collection_date}.'
                )
            else:
                # Actual update (not in dry-run mode)
                survey = self.get_or_create_survey(record)
                record.survey = survey
                record.save()
                logger.info(
                    f'Updated record ID {record.id} to Survey ID {survey.id} '
                    f'(date={survey.date}).'
                )

    def get_or_create_survey(self, record):
        """
        Find or create a Survey that has the same site and a date matching
        the record's collection_date.
        """
        surveys = Survey.objects.filter(
            date=record.collection_date,
            site=record.survey.site
        )

        if surveys.exists():
            survey = surveys.first()
            if surveys.count() > 1:
                logger.warning(
                    f'Multiple surveys found for site {record.survey.site.id} '
                    f'on {record.collection_date}. Using Survey ID {survey.id}.'
                )
        else:
            survey = Survey.objects.create(
                date=record.collection_date,
                site=record.survey.site,
                collector_string=record.survey.collector_string,
                uuid=record.survey.uuid,
                mobile=record.survey.mobile,
            )
            logger.info(f'Created new survey with ID {survey.id}.')

        return survey
