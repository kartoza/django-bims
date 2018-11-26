from django.core.management.base import BaseCommand
from django.contrib.gis.db import models
from bims.models.validation import Validation
from bims.models.biological_collection_record import (
    collection_post_save_update_cluster,
    collection_post_save_handler,
    BiologicalCollectionRecord
)


class Command(BaseCommand):
    """Update validation with new model.
    """

    def handle(self, *args, **options):
        # Get collection without taxa record
        collection_records = BiologicalCollectionRecord.objects.filter(
            validation__isnull=True
        )

        models.signals.post_save.disconnect(
                collection_post_save_update_cluster,
        )
        models.signals.post_save.disconnect(
                collection_post_save_handler,
        )

        print('Fix validations for %s collection records' %
              len(collection_records))

        for collection in collection_records:
            validation = Validation()
            if collection.validated:
                validation.validate()
            elif collection.ready_for_validation:
                validation.ready_for_validation = True
            validation.save()
            collection.validation = validation
            collection.save()

        print('Fixing validations finished')

        models.signals.post_save.connect(
                collection_post_save_update_cluster,
        )
        models.signals.post_save.connect(
                collection_post_save_handler,
        )
