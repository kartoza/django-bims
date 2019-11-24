# coding=utf-8
"""Add group to location context document."""
from django.core.management.base import BaseCommand
from bims.utils.location_context import get_location_context_data


class Command(BaseCommand):
    """Add group to location context document
    """

    def add_arguments(self, parser):
        parser.add_argument(
            '-i',
            '--only-empty',
            dest='only_empty',
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
        # 'political_boundary_group',
        # 'river_catchment_areas_group',
        # 'river_ecoregion_group',
        # 'water_management_area',
        # 'geomorphological_group',
        # 'monthly_mean_daily_average_temperature_group',
        # 'rainfall_group',
        # 'freshwater_ecoregion_of_the_world',
        # # 'critical_biodiversity_area',
        # 'national_freshwater_ecosystem_priority_area',
        # # 'strategic_water_source_areas'

        get_location_context_data(
            group_keys=options.get('groups', None),
            site_id=options.get('site_id', None),
            only_empty=options.get('only_empty', False)
        )
