from django.core.management import BaseCommand
from django.db.models import F
from bims.models import ChemicalRecord, Survey, LocationSite
from bims.utils.logger import log


class Command(BaseCommand):
    def handle(self, *args, **options):
        date_and_sites = ChemicalRecord.objects.filter(
            survey__isnull=True
        ).annotate(site=F('location_site')).values('site', 'date')
        index = 1
        for date_and_site in date_and_sites:
            log('{index}/{count}'.format(
                index=index,
                count=date_and_sites.count()))
            index += 1
            site = LocationSite.objects.get(id=date_and_site['site'])
            survey, survey_created = Survey.objects.get_or_create(
                site=site,
                date=date_and_site['date']
            )
            ChemicalRecord.objects.filter(
                location_site=site,
                date=date_and_site['date']
            ).update(survey=survey)
