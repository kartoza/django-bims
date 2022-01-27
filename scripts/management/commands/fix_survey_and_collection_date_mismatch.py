import logging

from bims.models.survey import Survey
from django.core.management import BaseCommand
from django.db.models import signals, F
from bims.models import (
    LocationSite,
    BiologicalCollectionRecord,
    location_site_post_save_handler,
    collection_post_save_handler
)

logger = logging.getLogger('bims')


class Command(BaseCommand):
    # Update location sites to use
    # legacy site codes if they have correct format

    def handle(self, *args, **options):
        signals.post_save.disconnect(
            location_site_post_save_handler
        )
        signals.post_save.disconnect(
            collection_post_save_handler
        )

        records = BiologicalCollectionRecord.objects.exclude(
            survey__date=F('collection_date')
        ).exclude(source_collection='gbif')

        logger.info(f'Total records {records.count()}')

        for record in records:
            try:
                survey = Survey.objects.get(
                    date=record.collection_date,
                    site=record.site
                )
                logger.info(f'Survey found {survey.id}')
            except Survey.DoesNotExist:
                logger.error('Survey does not exist, create one')
                survey = Survey.objects.create(
                    date=record.collection_date,
                    site=record.site,
                    validated=record.validated
                )
                logger.info(f'Survey created {survey.id}')
            except Survey.MultipleObjectsReturned:
                survey = Survey.objects.filter(
                    date=record.collection_date,
                    site=record.site
                ).first()
                logger.error(
                    f'Found multiple surveys, pick the first one {survey.id}')

            record.survey = survey
            record.save()


        signals.post_save.connect(
            collection_post_save_handler
        )
        signals.post_save.connect(
            location_site_post_save_handler
        )
