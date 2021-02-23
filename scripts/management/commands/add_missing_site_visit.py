# -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand
from django.db.models import signals
from bims.models import (
    BiologicalCollectionRecord, collection_post_save_handler
)
from bims.utils.logger import log


class Command(BaseCommand):

    def handle(self, *args, **options):
        signals.post_save.disconnect(
            collection_post_save_handler,
            sender=BiologicalCollectionRecord
        )
        collections = BiologicalCollectionRecord.objects.filter(
            survey__isnull=True
        )
        index = 0
        total = collections.count()
        for bio in collections:
            index += 1
            log('Processing {current}/{total}'.format(
                current=index,
                total=total
            ))
            bio.save()
        signals.post_save.connect(
            collection_post_save_handler,
            sender=BiologicalCollectionRecord
        )
