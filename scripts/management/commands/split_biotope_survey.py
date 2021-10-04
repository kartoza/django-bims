# -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand
from django.db.models import signals, Count
from bims.models import (
    BiologicalCollectionRecord, collection_post_save_handler, Survey, Biotope
)


class Command(BaseCommand):

    def handle(self, *args, **options):

        signals.post_save.disconnect(
            collection_post_save_handler,
            sender=BiologicalCollectionRecord
        )
        survey = Survey.objects.exclude(
            biological_collection_record__isnull=True)
        survey = survey.exclude(
            biological_collection_record__biotope__isnull=True)
        survey_with_multiple_biotope = survey.annotate(
            Count('biological_collection_record__biotope', distinct=True)
        ).filter(biological_collection_record__biotope__count__gt=1)

        for _survey in survey_with_multiple_biotope:
            biotope_list = Biotope.objects.filter(
                biologicalcollectionrecord__survey=_survey
            ).distinct()
            print('Splitting {}'.format(_survey))
            print('Biotope found : {}'.format(biotope_list))
            for biotope in biotope_list[1:]:
                print('Updating Biotope : {}'.format(biotope))
                bio = BiologicalCollectionRecord.objects.filter(
                    survey=_survey,
                    biotope=biotope
                )
                print('Assign {} collection records to new survey'.format(
                    bio.count()
                ))
                new_survey = Survey.objects.create(
                    site=_survey.site,
                    date=_survey.date,
                    validated=_survey.validated,
                    owner=_survey.owner,
                    collector_user=_survey.collector_user
                )
                bio.update(survey=new_survey)

        signals.post_save.connect(
            collection_post_save_handler,
            sender=BiologicalCollectionRecord
        )
