from django.core.management import BaseCommand
from django.db.models import F, CharField, Count
from django.db.models.functions import Concat
from bims.models import *



class Command(BaseCommand):
    """
    Combine duplicated surveys
    """

    def handle(self, *args, **options):
        qs = Survey.objects.annotate(dupe_id=Concat(F('site_id'), F('date'), F('owner_id'), output_field=CharField()))
        dupes = qs.values('dupe_id', 'site_id', 'date', 'owner_id').annotate(
            dupe_count=Count('dupe_id')).filter(dupe_count__gt=1)
        print('Total dupes : {}'.format(dupes.count()))

        for dupe in dupes:
            surveys = Survey.objects.filter(site=dupe['site_id'],
                                           date=dupe['date'],
                                           owner_id=dupe['owner_id'])
            site = LocationSite.objects.filter(
                id=dupe['site_id']
            )
            bio = BiologicalCollectionRecord.objects.filter(
                survey__in=surveys
            )
            algae_data = AlgaeData.objects.filter(
                survey__in=surveys
            )
            chemical_records = ChemicalRecord.objects.filter(
                survey__in=surveys
            )
            print('Merging {bio} records for {survey} surveys - {site}'.format(
                bio = bio.count(),
                survey = surveys.count(),
                site = site[0].location_site_identifier
            ))
            _survey = surveys[0]
            bio.update(survey=_survey)
            algae_data.update(survey=_survey)
            chemical_records.update(survey=_survey)
            surveys.exclude(id=_survey.id).delete()

