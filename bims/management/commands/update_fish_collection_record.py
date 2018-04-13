from django.core.management.base import BaseCommand
from bims.utils.gbif import update_fish_collection_record
from bims.models import BiologicalCollectionRecord


class Command(BaseCommand):
    """Update Fish Collection Record.
    """

    def handle(self, *args, **options):
        collections = BiologicalCollectionRecord.objects.all()
        for record in collections:
            print('Update record : %s' % record.original_species_name)
            update_fish_collection_record(record)
