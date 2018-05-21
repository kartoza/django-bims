# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand
from bims.management.commands.update_boundary import (
    UpdateBoundary
)


class Command(UpdateBoundary, BaseCommand):
    help = 'Import countries from CSV file'

    def handle(self, *args, **options):
        self.save_data(
            shapefile='bims/data/country/ne_10m_admin_0_countries.shp',
            boundary_type='country',
            column_name='NAME')
