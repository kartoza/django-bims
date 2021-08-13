# -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand

from bims.utils.logger import log
from bims.models.survey import Survey
from sass.models import (
    SassTaxon,
    SiteVisitBiotopeTaxon,
    SiteVisitTaxon,
    SiteVisit
)


class Command(BaseCommand):

    def handle(self, *args, **options):
        site_visit_taxon = SiteVisitTaxon.objects.all()
        site_visit = SiteVisit.objects.filter(
            id__in=site_visit_taxon.values_list('site_visit')
        ).order_by('id').distinct('id')
        survey = Survey.objects.filter(
            id__in=site_visit_taxon.values_list('survey')
        ).order_by('id').distinct('id')
        print(site_visit.count())
        print(survey.count())
        print(site_visit.count() == survey.count())
        for sv in site_visit:
            site_visit_taxon = SiteVisitTaxon.objects.filter(
                site_visit=sv)
            print(site_visit_taxon.count())
            surveys = site_visit_taxon.values('survey').distinct('survey')
            if surveys.count() > 1:
                correct_survey = surveys[0]
                surveys.exclude(id=correct_survey.id).count()
            print(surveys.count())