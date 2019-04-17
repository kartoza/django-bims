# coding=utf-8
"""Get river name for location sites"""

from django.core.management.base import BaseCommand
from bims.models.location_site import (
    LocationSite,
)
from bims.location_site.river import (
    allocate_site_codes_from_river
)
from bims.utils.logger import log


class Command(BaseCommand):
    """Fetch river name for location sites
    """

    def add_arguments(self, parser):
        parser.add_argument(
            '-c',
            '--clear-site-code',
            dest='clear_site_code',
            default=False,
            help='Should clear all site codes')

    def handle(self, *args, **options):
        clear_site_code = options.get('clear_site_code')
        if clear_site_code:
            LocationSite.objects.filter(
                river__isnull=False
            ).update(
                site_code=''
            )
        location_sites = LocationSite.objects.filter(
            site_code__exact='',
            river__isnull=False
        )

        index = 0
        for location_site in location_sites:
            log('processing %s of %s' % (
                index,
                len(location_sites)
            ))
            index += 1
            # Allocate site code
            allocate_site_codes_from_river(
                update_site_code=True,
                location_id=location_site.id
            )
