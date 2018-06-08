# -*- coding: utf-8 -*-

import os
from django.conf import settings
from django.core.management.base import BaseCommand
from bims.management.commands.update_boundary import (
    UpdateBoundary
)


class Command(UpdateBoundary, BaseCommand):
    help = 'Import countries from shp file'

    def handle(self, *args, **options):
        self.save_data(
            os.path.join(
                settings.STATIC_ROOT,
                'data/country/ne_10m_admin_0_countries.shp'
            ),
            'country', 'NAME')
