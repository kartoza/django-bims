# coding=utf-8
"""Get river name for location sites"""
import ast
from django.core.management.base import BaseCommand
from django.db.models import Q
from bims.models.location_site import (
    LocationSite,
)
from bims.location_site.river import (
    fetch_river_name,
    allocate_site_codes_from_river
)
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
        parser.add_argument(
            '-a',
            '--allocate-site-code',
            dest='allocate_site_code',
            default=None,
            help='Allocate site code')

    def handle(self, *args, **options):
        location_site_id = options.get('location_site_id')
        allocate_site_code = ast.literal_eval(
            options.get('allocate_site_code', 'True')
        )
        if location_site_id:
            location_sites = LocationSite.objects.filter(id=location_site_id)
        else:
            location_sites = LocationSite.objects.filter(
                Q(river__isnull=True) | Q(river__name='')
            )
        index = 1
        for location_site in location_sites:
            print('Fetch river name for [{site}] ({current}/{len})'.format(
                site=location_site.id,
                current=index,
                len=location_sites.count()
            ))
            index += 1
            river_name = fetch_river_name(
                location_site.latitude,
                location_site.longitude
            )
            if not river_name:
                print('Got empty river name from geocontext')
                continue
            try:
                river, created = River.objects.get_or_create(
                    name=river_name
                )
            except River.MultipleObjectsReturned:
                river = River.objects.filter(name=river_name)[0]
            location_site.river = river
            location_site.save()

            # Allocate site code
            if allocate_site_code:
                allocate_site_codes_from_river(
                    update_site_code=True,
                    location_id=location_site.id
                )
