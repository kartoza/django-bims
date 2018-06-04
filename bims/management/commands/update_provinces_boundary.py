# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand
from bims.management.commands.update_boundary import (
    UpdateBoundary
)


class Command(UpdateBoundary, BaseCommand):
    help = 'Import provinces from shp file'

    def handle(self, *args, **options):
        self.save_data(
            'bims/data/province/province_boundary.shp',
            'province', 'provname')
