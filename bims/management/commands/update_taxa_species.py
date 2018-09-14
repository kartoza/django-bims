from django.core.management.base import BaseCommand
from django.contrib.gis.db import models
from django.db.models import Q
from bims.utils.gbif import update_collection_record
from bims.models.biological_collection_record import (
    BiologicalCollectionRecord,
    collection_post_save_update_cluster,
    collection_post_save_handler
)


class Command(BaseCommand):
    """Update taxa.
    """
    def add_arguments(self, parser):
        parser.add_argument(
            '-oc',
            '--only-update-missing-class',
            dest='only_update_missing_class',
            default=False,
            help='Only update missing class')

    def handle(self, *args, **options):
        # Get collection without taxa record
        only_update_missing_class = options.get('only_update_missing_class')
        if only_update_missing_class:
            collections_non_taxa = BiologicalCollectionRecord.objects.filter(
                    Q(taxon_gbif_id__taxon_class__isnull=True) |
                    Q(taxon_gbif_id__taxon_class__exact='')
            )
        else:
            collections_non_taxa = BiologicalCollectionRecord.objects.filter(
                    taxon_gbif_id__isnull=True
            )
        models.signals.post_save.disconnect(
                collection_post_save_update_cluster,
        )
        models.signals.post_save.disconnect(
                collection_post_save_handler,
        )
        for collection in collections_non_taxa:
            existed = BiologicalCollectionRecord.objects.filter(
                original_species_name=collection.original_species_name,
                taxon_gbif_id__isnull=False
            )
            if existed and not only_update_missing_class:
                collection.taxon_gbif_id = existed[0].taxon_gbif_id
                collection.save()
            else:
                update_collection_record(collection)

        models.signals.post_save.connect(
                collection_post_save_update_cluster,
        )
        models.signals.post_save.connect(
                collection_post_save_handler,
        )
