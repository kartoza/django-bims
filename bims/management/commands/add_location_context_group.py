# coding=utf-8
"""Add group to location context document."""

from django.core.management.base import BaseCommand
from django.contrib.gis.db import models
from bims.models.location_site import (
    LocationSite,
    location_site_post_save_handler,
)


class Command(BaseCommand):
    """Add group to location context document
    """

    def add_arguments(self, parser):
        parser.add_argument(
            '-i',
            '--ignore-not-empty',
            dest='ignore_not_empty',
            default=False,
            help='Only update empty location context')

    def handle(self, *args, **options):

        geocontext_group_keys = [
            "political_boundary_group",
            "cadastre_group",
            # "elevation_group",
            # "water_group",
            # "rainfall_group",
            # "land_cover_group",
            # "vegetation_group",
            # "monthly_mean_daily_maximum_temperature_group",
            # "monthly_mean_daily_average_temperature_group",
            # "monthly_mean_daily_average_relative_humidity_group",
            # "monthly_standard_deviation_daily_maximum_temperature_group",
            # "monthly_standard_deviation_daily_maximum_relative_humidity_group",
            # "monthly_standard_deviation_of_daily_mean_temperature_group",
            # "monthly_means_of_daily_minimum_temperature_group",
            # "monthly_standard_deviation_of_daily_minimum_temperature_group"
        ]

        ignore_not_empty = options.get('ignore_not_empty')
        if ignore_not_empty:
            location_sites = LocationSite.objects.filter(
                location_context_document__isnull=True,
            )
        else:
            location_sites = LocationSite.objects.all()
        num = len(location_sites)
        i = 1

        models.signals.post_save.disconnect(
            location_site_post_save_handler,
        )
        success = True
        for location_site in location_sites:
            print('Updating %s of %s, %s' % (i, num, location_site.name))
            i += 1
            for group_key in geocontext_group_keys:
                current_outcome, message = location_site.add_context_group(group_key)
                success = success * current_outcome
            if not success:
                print('[FAILED] %s : %s' % (location_site.name, message))
            if success:
                location_site.save()

        models.signals.post_save.connect(
            location_site_post_save_handler,
        )
