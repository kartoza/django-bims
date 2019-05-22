# -*- coding: utf-8 -*-
import json

from django.core.management.base import BaseCommand
from django.db import models

from bims.utils.logger import log
from bims.models import LocationSite, location_site_post_save_handler


class Command(BaseCommand):
    """
    Move site name to site description, move site description to
    additional_data.comment
    """

    def handle(self, *args, **options):
        sites = LocationSite.objects.filter(
            biological_collection_record__notes__icontains='sass',
            biological_collection_record__source_collection__icontains='fbis',
        ).distinct()
        index = 0
        models.signals.post_save.disconnect(
            location_site_post_save_handler,
        )
        for site in sites:
            index += 1
            log('Processing {0}/{1}'.format(
                index,
                sites.count()
            ))
            additional_data = json.loads(site.additional_data)
            additional_data['comment'] = site.site_description
            site.additional_data = additional_data
            site.site_description = site.name
            site.save()
        models.signals.post_save.connect(
            location_site_post_save_handler,
        )
