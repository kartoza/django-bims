import os
import re

from django.core.management import BaseCommand
from django.contrib.sites.models import Site


class Command(BaseCommand):

    def handle(self, *args, **options):
        site_url = os.environ.get('SITEURL', '')
        if site_url:
            site = Site.objects.get_current()
            domains = re.findall(
                "^(?:https?:\/\/)?(?:[^@\/\n]+@)?(?:www\.)?([^\/?\n]+)",
                site_url
            )
            if domains and len(domains) > 0:
                site.domain = domains[0]
            site.save()
