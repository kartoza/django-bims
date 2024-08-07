from django.core.management.base import BaseCommand
from bims.tasks.source_reference import (
    generate_source_reference_filter
)


class Command(BaseCommand):
    """Generate permissions for all taxon class
    """

    def handle(self, *args, **options):
        generate_source_reference_filter()
