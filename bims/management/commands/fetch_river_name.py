# coding=utf-8
"""Get river name for location sites"""

from django.core.management.base import BaseCommand
from bims.models.location_site import (
    LocationSite,
)
from bims.location_site.river import fetch_river_name
from sass.models.river import River


class Command(BaseCommand):
    """Fetch river name for location sites
    """

    def add_arguments(self, parser):
        parser.add_argument(
            '-s',
            '--location-site',
            dest='location_site_id',
            default=None,
            help='Id of location site')

    def handle(self, *args, **options):
        location_site_id = options.get('location_site_id')
        if location_site_id:
            location_sites = LocationSite.objects.filter(id=location_site_id)
        else:
            location_sites = LocationSite.objects.filter(
                river__isnull=True
            )

        for location_site in location_sites:
            print('Fetch river name for [{}]'.format(
                location_site.id
            ))
            river_name = fetch_river_name(location_site)
            if not river_name:
                print('Got empty river name from geocontext')
                continue
            river, created = River.objects.get_or_create(
                name=river_name
            )
            location_site.river = river
            location_site.save()
