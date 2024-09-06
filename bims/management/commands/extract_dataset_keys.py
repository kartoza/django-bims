# -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand
from bims.scripts.extract_dataset_keys import (
    extract_dataset_keys
)


class Command(BaseCommand):

    def handle(self, *args, **options):
        extract_dataset_keys()
