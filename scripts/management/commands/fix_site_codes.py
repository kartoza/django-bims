from django.core.management import BaseCommand
from django.db.models import signals
from bims.models import LocationSite, location_site_post_save_handler
from bims.utils.logger import log
from bims.location_site.river import (
    allocate_site_codes_from_river
)


class Command(BaseCommand):
    # Update location sites to use
    # legacy site codes if they have correct format

    def handle(self, *args, **options):
        location_sites = LocationSite.objects.exclude(
            site_code__iregex=r'([A-Za-z0-9]){1,6}-([A-Za-z0-9]*)$'
        )

        log('Update {} location site(s)'.format(
            location_sites.count()
        ))

        signals.post_save.disconnect(
            location_site_post_save_handler
        )

        index = 0
        for location_site in location_sites:
            log('processing %s of %s' % (
                index,
                location_sites.count()
            ))
            index += 1
            # Allocate site code
            allocate_site_codes_from_river(
                update_site_code=True,
                location_id=location_site.id
            )

        signals.post_save.connect(
            location_site_post_save_handler
        )
