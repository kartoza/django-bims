# coding=utf-8
"""Update location context document."""

from django.core.management.base import BaseCommand
from bims.models.location_site import LocationSite


class Command(BaseCommand):
    """Update location site context document
    """

    def handle(self, *args, **options):
        location_sites = LocationSite.objects.all()
        num = LocationSite.objects.count()
        i = 1
        for location_site in location_sites:
            print('Updating %s of %s, %s' % (i, num, location_site.name))
            i += 1
            success, message = location_site.update_location_context_document()
            if not success:
                print('[FAILED] %s : %s' % (location_site.name, message))
            if success:
                location_site.save()
