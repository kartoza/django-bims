# -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand

from bims.utils.location_site import allocate_site_codes_from_river


class Command(BaseCommand):

    def handle(self, *args, **options):
        # Call allocate site code function
        allocate_site_codes_from_river()
