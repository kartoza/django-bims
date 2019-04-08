# coding=utf-8
"""Add group to location context document."""
import json
from django.core.management.base import BaseCommand
from django.db.models import Q
from bims.models.location_site import (
    LocationSite,
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

        parser.add_argument(
            '-g',
            '--groups',
            dest='groups',
            default=None,
            help='Geocontext groups keys')

        parser.add_argument(
            '-s',
            '--site-id',
            dest='site_id',
            default=None,
            help='Update location context for specific site')

    def handle(self, *args, **options):

        groups = options.get('groups', None)
        if groups:
            geocontext_group_keys = groups.split(',')
        else:
            geocontext_group_keys = [
                "political_boundary_group",
                "cadastre_group",
                "elevation_group",
                "water_group",
                "rainfall_group",
                "land_cover_group",
                "vegetation_group",
                "monthly_mean_daily_maximum_temperature_group",
                "monthly_mean_daily_average_temperature_group",
                "monthly_mean_daily_average_relative_humidity_group",
                "monthly_standard_deviation_daily_maximum_temperature_group",
                "monthly_standard_deviation_daily_"
                "maximum_relative_humidity_group",
                "monthly_standard_deviation_of_daily_mean_temperature_group",
                "monthly_means_of_daily_minimum_temperature_group",
                "monthly_standard_deviation_of_"
                "daily_minimum_temperature_group",
                "eco_geo_group"
            ]

        ignore_not_empty = options.get('ignore_not_empty')
        site_id = options.get('site_id', None)
        if site_id:
            site_id = site_id.split(',')

        if ignore_not_empty:
            ignored_filters = None
            for group_key in geocontext_group_keys:
                if ignored_filters is None:
                    ignored_filters = Q(
                        **{'location_context__'
                            'context_group_values__{}__isnull'.
                            format(group_key): True}
                    )
                else:
                    ignored_filters = ignored_filters | Q(
                        **{'location_context__'
                            'context_group_values__{}__isnull'.
                            format(group_key): True}
                    )
            location_sites = LocationSite.objects.filter(ignored_filters)
        else:
            location_sites = LocationSite.objects.all()

        if site_id:
            location_sites = location_sites.filter(id__in=site_id)

        num = len(location_sites)
        i = 1

        for location_site in location_sites:
            print('Updating %s of %s, %s' % (i, num, location_site.name))
            i += 1
            all_context = None
            if ignore_not_empty:
                try:
                    all_context = json.loads(location_site.location_context)
                except (ValueError, TypeError):
                    pass
            for group_key in geocontext_group_keys:
                if (all_context and
                        group_key in all_context['context_group_values']):
                    print('Context data already exists for {}'.format(
                        group_key
                    ))
                    continue
                current_outcome, message = (
                    location_site.add_context_group(group_key))
                success = current_outcome
                print('[{status}] [{site_id}] [{group}] - {message}'.format(
                    status='SUCCESS' if success else 'FAILED',
                    site_id=location_site.id,
                    message=message,
                    group=group_key
                ))
                if success:
                    location_site.save()
