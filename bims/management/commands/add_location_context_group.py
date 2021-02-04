# coding=utf-8
"""Add group to location context document."""
import ast
from django.core.management.base import BaseCommand
from django.db.models import signals
from bims.utils.location_context import get_location_context_data
from bims.models.location_context_group import (
    LocationContextGroup
)


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

        parser.add_argument(
            '-sc',
            '--site-code',
            dest='site_code',
            default='False',
            help='Generate site code')

    def handle(self, *args, **options):

        signals.post_save.disconnect(
            sender=LocationContextGroup
        )

        generate_site_code = ast.literal_eval(
            options.get('site_code')
        )

        get_location_context_data(
            group_keys=options.get('groups', None),
            site_id=options.get('site_id', None),
            only_empty=options.get('only_empty', False),
            should_generate_site_code=generate_site_code
        )
