# -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand
from django.db.models import Subquery, OuterRef

from bims.models import (
    Survey
)
from sass.models import (
    SiteVisitTaxon
)


class Command(BaseCommand):

    def handle(self, *args, **options):
        site_visit_taxa = SiteVisitTaxon.objects.all()
        survey = Survey.objects.filter(
            biological_collection_record__in=site_visit_taxa)
        survey.update(owner=Subquery(
            site_visit_taxa.filter(survey__pk=OuterRef('pk')).values(
                'site_visit__owner')[:1]))
