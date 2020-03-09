# coding=utf-8
"""Get river name for location sites"""
import ast
from django.core.management.base import BaseCommand
from django.db.models import F
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
        parser.add_argument(
            '-r',
            '--restore-legacy-site-code',
            dest='restore_legacy_site_code',
            default=False,
            help='Restore legacy site code'
        )
        parser.add_argument(
            '-u',
            '--update-site-codes',
            dest='update_site_codes',
            default='True',
            help='Should also update existing site codes')


    def handle(self, *args, **options):
        clear_site_code = options.get('clear_site_code')
        restore_legacy_site_code = options.get('restore_legacy_site_code')
        update_site_codes = ast.literal_eval(
            options.get('update_site_codes')
        )
        if clear_site_code:
            location_site_to_clear = LocationSite.objects.filter(
                river__isnull=False
            )
            log('Clear site code for for {} sites'.format(
                location_site_to_clear.count()
            ))
            location_site_to_clear.update(
                site_code=''
            )

        if restore_legacy_site_code:
            sites_with_legacy_site_code = LocationSite.objects.filter(
                legacy_site_code__isnull=False
            ).exclude(legacy_site_code='')
            log('Restoring legacy site code for {} sites'.format(
                sites_with_legacy_site_code.count()
            ))
            sites_with_legacy_site_code.update(
                site_code=F('legacy_site_code')
            )

        location_sites = LocationSite.objects.filter(
            site_code__exact='',
            river__isnull=False
        )

        index = 0
        for location_site in location_sites:
            log('processing %s of %s' % (
                index,
                location_sites.count()
            ))
            index += 1
            # Allocate site code
            allocate_site_codes_from_river(
                update_site_code=update_site_codes,
                location_id=location_site.id
            )
