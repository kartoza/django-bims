from django.core.management.base import BaseCommand
from bims.utils.gbif import update_taxa


class Command(BaseCommand):
    """Update taxa.
    """

    def handle(self, *args, **options):
        update_taxa()
