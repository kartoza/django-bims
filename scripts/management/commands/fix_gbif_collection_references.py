from django.core.management import BaseCommand
from django.db.models import signals
from bims.models import (
    BiologicalCollectionRecord,
    collection_post_save_handler,
)
from bims.utils.user import create_users_from_string
from bims.utils.logger import log


class Command(BaseCommand):
    def handle(self, *args, **options):
        signals.post_save.disconnect(
            collection_post_save_handler,
            sender=BiologicalCollectionRecord
        )

        # Get all collections that came from gbif and have reference
        collections = BiologicalCollectionRecord.objects.filter(
            additional_data__fetch_from_gbif=True
        ).exclude(reference__iexact='')

        index = 0
        for collection in collections:
            index += 1
            log('Processing : {index}/{len}'.format(
                index=index,
                len=collections.count()
            ))

            if collection.collector and not collection.collector_user:
                users = create_users_from_string(collection.collector)
                if len(users) > 0:
                    log('Update owner and collector to {}'.format(
                        users[0].username
                    ))
                    collection.collector_user = users[0]
                    collection.owner = users[0]

            collection.save()
