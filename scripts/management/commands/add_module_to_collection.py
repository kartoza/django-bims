# -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand
from bims.models import BiologicalCollectionRecord
from bims.utils.logger import log


class Command(BaseCommand):

    def handle(self, *args, **options):
        collections = BiologicalCollectionRecord.objects.filter(
            module_group__isnull=True
        )
        index = 0
        for bio in collections:
            index += 1
            log('Processing {current}/{total}'.format(
                current=index,
                total=collections.count()
            ))
            bio.save()
