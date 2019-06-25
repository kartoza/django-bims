# -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand
from sass.models import (
    SiteVisit,
)
from sass.scripts.site_visit_ecological_condition_generator import (
    generate_site_visit_ecological_condition
)


class Command(BaseCommand):

    def handle(self, *args, **options):
        site_visits = SiteVisit.objects.filter(
            location_site__site_code='G2KALK-UPSTR'
        )
        generate_site_visit_ecological_condition(site_visits)
