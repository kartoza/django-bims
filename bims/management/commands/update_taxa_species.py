from django.core.management.base import BaseCommand
from bims.utils.gbif import update_collection_record
from bims.models.biological_collection_record import BiologicalCollectionRecord


class Command(BaseCommand):
    """Update taxa.
    """

    def handle(self, *args, **options):
        # Get collection without taxa record
        collections_non_taxa = BiologicalCollectionRecord.objects.filter(
                taxon_gbif_id__isnull=True
        )
        for collection in collections_non_taxa:
            existed = BiologicalCollectionRecord.objects.filter(
                original_species_name=collection.original_species_name,
                taxon_gbif_id__isnull=False
            )
            if existed:
                collection.taxon_gbif_id = existed[0].taxon_gbif_id
            else:
                update_collection_record(collection)
