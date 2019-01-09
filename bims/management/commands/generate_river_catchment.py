from django.core.management.base import BaseCommand
from bims.utils.river_catchments import generate_river_catchments


class Command(BaseCommand):
    """Update taxa.
    """

    def handle(self, *args, **options):
        generate_river_catchments()
