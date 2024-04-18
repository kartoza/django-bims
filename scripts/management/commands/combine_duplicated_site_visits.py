import ast

from django.core.management import BaseCommand
from django.db.models import F, CharField, Count
from django.db.models.functions import Concat
from bims.models import *


class Command(BaseCommand):
    """
    Combine duplicated surveys
    """
    def add_arguments(self, parser):
        parser.add_argument(
            '-s',
            '--site_id',
            dest='site_id',
            default=None,
        )
        parser.add_argument(
            '-fsd',
            '--fix_survey_date',
            dest='fix_survey_date',
            default='False',
        )

    def handle(self, *args, **options):
        site_id = options.get('site_id', None)
        fix_survey_date = ast.literal_eval(options.get('fix_survey_date', 'False'))
        if site_id:
            Site.objects.get(id=site_id)
        else:
            Site.objects.first()

        qs = Survey.objects.all()
        qs = qs.annotate(dupe_id=Concat(
            F('site_id'),
            F('date'),
            F('owner_id'), output_field=CharField()))
        dupes = qs.values('dupe_id', 'site_id', 'date', 'owner_id').annotate(
            dupe_count=Count('dupe_id')).filter(dupe_count__gt=1)
        for dupe in dupes:
            surveys = Survey.objects.filter(
                site=dupe['site_id'],
                date=dupe['date'],
                owner_id=dupe['owner_id'])
            site = LocationSite.objects.filter(
                id=dupe['site_id']
            )
            bio = BiologicalCollectionRecord.objects.filter(
                Q(source_site_id=site_id) | Q(additional_observation_sites=site_id),
                survey__in=surveys,
            )
            if bio.count() == 0:
                continue
            algae_data = AlgaeData.objects.filter(
                survey__in=surveys,
            )
            chemical_records = ChemicalRecord.objects.filter(
                survey__in=surveys
            )
            print('Merging {bio}/{algae}/{cr} records for {survey} surveys - {site} - {date}'.format(
                bio=bio.count(),
                algae=algae_data.count(),
                cr=chemical_records.count(),
                survey=surveys.count(),
                site=site[0].location_site_identifier,
                date=surveys.first().date
            ))
            _survey = surveys[0]
            with transaction.atomic():
                if fix_survey_date and bio.exists():
                    surveys.update(
                        date=bio.first().collection_date
                    )

                bio.update(survey=_survey)
                algae_data.update(survey=_survey)
                chemical_records.update(survey=_survey)
                surveys.exclude(id=_survey.id).delete()
