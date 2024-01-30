# for issue https://github.com/kartoza/django-bims/issues/3491
from django.core.management import BaseCommand
from django.db.models import signals, Count
from bims.models import (
    location_site_post_save_handler,
    location_context_post_save_handler, LocationContextGroup,
    LocationContextFilter, LocationContextFilterGroupOrder,
    BiologicalCollectionRecord
)


class Command(BaseCommand):
    # Update location sites to use
    # legacy site codes if they have correct format

    def handle(self, *args, **options):
        # Query
        records_with_multiple_module_groups = BiologicalCollectionRecord.objects.values(
            'survey'
        ).annotate(
            module_group_count=Count('module_group', distinct=True)
        ).filter(
            module_group_count__gt=1
        )

        signals.post_save.disconnect(
            location_site_post_save_handler
        )
        signals.post_save.disconnect(
            location_context_post_save_handler,
            sender=LocationContextGroup
        )
        signals.post_save.disconnect(
            location_context_post_save_handler,
            sender=LocationContextFilter
        )
        signals.post_save.disconnect(
            location_context_post_save_handler,
            sender=LocationContextFilterGroupOrder
        )

        index = 0

        for record in records_with_multiple_module_groups:
            bio_records = BiologicalCollectionRecord.objects.filter(
                survey=record['survey']
            )
            survey = bio_records.first().survey
            module_groups = list(bio_records.values_list(
                'module_group', flat=True
            ).distinct())
            print('old survey : {}'.format(survey.id))
            for module_group in module_groups[1:]:
                survey.pk = None
                survey.save()
                bio_records.filter(
                    module_group=module_group
                ).update(survey=survey)
                print('new survey : {}'.format(survey.id))

        signals.post_save.connect(
            location_site_post_save_handler
        )
        signals.post_save.connect(
            location_context_post_save_handler,
            sender=LocationContextGroup
        )
        signals.post_save.connect(
            location_context_post_save_handler,
            sender=LocationContextFilter
        )
        signals.post_save.connect(
            location_context_post_save_handler,
            sender=LocationContextFilterGroupOrder
        )
