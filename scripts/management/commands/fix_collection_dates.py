import logging
from django.core.management.base import BaseCommand
from bims.models import BiologicalCollectionRecord, Survey
from django.db.models import F
from django.db import transaction

logger = logging.getLogger(__name__)

BATCH_SIZE = 1000


class Command(BaseCommand):
    help = 'Ensure BiologicalCollectionRecord collection_date matches Survey date'

    def handle(self, *args, **kwargs):
        self.fix_collection_dates()

    def fix_collection_dates(self):
        mismatched_records = BiologicalCollectionRecord.objects.exclude(
            collection_date=F('survey__date')
        )

        record_count = mismatched_records.count()
        logger.info(f'Found {record_count} records with mismatched dates')

        if record_count == 0:
            return

        with transaction.atomic():
            for start in range(0, record_count, BATCH_SIZE):
                batch = mismatched_records[start:start + BATCH_SIZE]
                self.process_batch(batch)

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
