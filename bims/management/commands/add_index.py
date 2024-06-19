# -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand
from bims.utils.add_index import add_indexes_for_taxonomy


class Command(BaseCommand):

    def handle(self, *args, **options):
        add_indexes_for_taxonomy()
