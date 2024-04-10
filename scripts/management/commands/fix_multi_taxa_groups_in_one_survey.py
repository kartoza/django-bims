from django.core.management.base import BaseCommand
from django.db.models import Count
from django.db import transaction
from django.db.models.signals import post_save
from contextlib import contextmanager
import logging

from bims.models import (
    BiologicalCollectionRecord,
    LocationContextGroup,
    LocationContextFilter,
    LocationContextFilterGroupOrder,
    location_site_post_save_handler,
    location_context_post_save_handler,
)

logger = logging.getLogger(__name__)


@contextmanager
def signal_handler_disconnect():
    """
    Temporarily disconnects signal handlers for the duration of the context.
    """
    post_save.disconnect(location_site_post_save_handler)
    post_save.disconnect(location_context_post_save_handler, sender=LocationContextGroup)
    post_save.disconnect(location_context_post_save_handler, sender=LocationContextFilter)
    post_save.disconnect(location_context_post_save_handler, sender=LocationContextFilterGroupOrder)
    try:
        yield
    finally:
        post_save.connect(location_site_post_save_handler)
        post_save.connect(location_context_post_save_handler, sender=LocationContextGroup)
        post_save.connect(location_context_post_save_handler, sender=LocationContextFilter)
        post_save.connect(location_context_post_save_handler, sender=LocationContextFilterGroupOrder)


class Command(BaseCommand):
    help = "Update location sites to use legacy site codes if they have the correct format."

    def handle(self, *args, **options):
        with signal_handler_disconnect(), transaction.atomic():
            self.process_records()

    def process_records(self):
        """
        Identifies records with multiple module groups and updates their survey references.
        """
        records_with_multiple_module_groups = BiologicalCollectionRecord.objects.values(
            'survey'
        ).annotate(
            module_group_count=Count('module_group', distinct=True)
        ).filter(
            module_group_count__gt=1
        )

        for record in records_with_multiple_module_groups:
            self.update_survey_records(record)

    def update_survey_records(self, record):
        """
        Updates survey records for a given record with multiple module groups.
        """
        bio_records = BiologicalCollectionRecord.objects.filter(
            survey=record['survey']
        )
        first_record = bio_records.first()
        if not first_record:
            logger.error('No BiologicalCollectionRecord found for survey: %s', record['survey'])
            return

        survey = first_record.survey

        if survey is None:
            logger.error(
                'Survey is None for BiologicalCollectionRecord with survey: %s', record['survey'])
            return

        module_groups = list(bio_records.values_list(
            'module_group', flat=True
        ).distinct())

        logger.info('Old survey ID: %s', survey.id)
        for module_group in module_groups[1:]:
            survey.pk = None
            survey.save()
            bio_records.filter(
                module_group=module_group
            ).update(survey=survey)
            logger.info('New survey ID: %s', survey.id)
