# coding=utf-8
"""Update location context document."""

from django.core.management.base import BaseCommand
from django.contrib.gis.db import models
from bims.models.location_site import (
    LocationSite,
    location_site_post_save_handler,
)


class Command(BaseCommand):
    """Update location site context document
    """

    def add_arguments(self, parser):
        parser.add_argument(
            '-i',
            '--ignore-not-empty',
            dest='ignore_not_empty',
            default=False,
            help='Only update empty location context')


    def handle(self, *args, **options):
        ignore_not_empty = options.get('ignore_not_empty')
        if ignore_not_empty:
            location_sites = LocationSite.objects.filter(
                location_context_document__isnull=True,
            )
        else:
            location_sites = LocationSite.objects.filter(id=9344)
        num = len(location_sites)
        i = 1

        models.signals.post_save.disconnect(
            location_site_post_save_handler,
        )

        for location_site in location_sites:
            print('Updating %s of %s, %s' % (i, num, location_site.name))
            i += 1
            success, message = location_site.update_location_context_document()
            if not success:
                print('[FAILED] %s : %s' % (location_site.name, message))
            if success:
                location_site.save()

        models.signals.post_save.connect(
            location_site_post_save_handler,
        )
