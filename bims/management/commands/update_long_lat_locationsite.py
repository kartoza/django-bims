from django.core.management.base import BaseCommand
from django.contrib.gis.db import models
from django.db.models import Q
from bims.models.location_site import (
    location_site_post_save_handler,
    LocationSite
)


class Command(BaseCommand):
    """Update taxa.
    """

    def handle(self, *args, **options):
        # Update lon lat
        location_sites = LocationSite.objects.filter(
            Q(longitude__isnull=True) |
            Q(latitude__isnull=True)
        )

        print('Updating: %s' % len(location_sites))

        models.signals.post_save.disconnect(
                location_site_post_save_handler,
        )

        for site in location_sites:
            center = site.get_centroid()
            site.longitude = center.x
            site.latitude = center.y
            site.save()

        models.signals.post_save.connect(
                location_site_post_save_handler,
        )
