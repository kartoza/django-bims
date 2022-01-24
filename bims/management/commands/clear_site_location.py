from bims.models.location_site import LocationSite

from bims.models.biological_collection_record import BiologicalCollectionRecord
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    """Delete location site which do not have collection record
    """

    def handle(self, *args, **options):
        collection_records = BiologicalCollectionRecord.objects.all().values('site_id')
        site_location = LocationSite.objects.exclude(pk__in=collection_records)
        print('Delete site location')
        site_location.delete()
