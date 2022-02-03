# coding=utf-8
"""Add group to location context document."""
import ast
import logging
from bims.models.location_site import LocationSite, generate_site_code
from django.core.management.base import BaseCommand

from bims.signals.utils import disconnect_bims_signals, connect_bims_signals

logger = logging.getLogger('bims')


class Command(BaseCommand):
    """Add site codes
    """

    def add_arguments(self, parser):
        parser.add_argument(
            '-om',
            '--only-missing',
            dest='only_missing',
            default='False',
            help='Only add site code to sites without site code')

    def handle(self, *args, **options):

        disconnect_bims_signals()

        only_missing = ast.literal_eval(
            options.get('only_missing', 'False')
        )

        if only_missing:
            sites = LocationSite.objects.filter(site_code='')
        else:
            sites = LocationSite.objects.all()

        logger.info(f'Add site code to {sites.count()} sites')
        index = 1

        for location_site in sites:
            logger.info(f'{index}/{sites.count()} - '
                        f'Generate a site code for {location_site.id}')
            site_code, catchments_data = generate_site_code(
                location_site,
                lat=location_site.latitude,
                lon=location_site.longitude
            )
            logger.info(f'New site code {site_code}')
            location_site.site_code = site_code
            location_site.save()

        connect_bims_signals()
