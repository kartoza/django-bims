import os
from django.core.management.base import BaseCommand
from django.conf import settings
from bims.tasks.location_context import generate_spatial_scale_filter


class Command(BaseCommand):
    """Generate permissions for all taxon class
    """

    def handle(self, *args, **options):
        file_name = 'spatial_scale_filter_list.txt'
        file_path = os.path.join(
            settings.MEDIA_ROOT,
            file_name
        )
        generate_spatial_scale_filter(file_path)
