from django.core.management import BaseCommand
from django.db.models import F, signals
from bims.models import LocationSite, location_site_post_save_handler
from bims.utils.logger import log

class Command(BaseCommand):
    # Update location sites to use
    # legacy site codes if they have correct format

    def handle(self, *args, **options):
        location_sites = LocationSite.objects.filter(
            legacy_site_code__iregex=r'([A-Za-z0-9]){1,6}-([A-Za-z]*)$'
        ).exclude(
            site_code=F('legacy_site_code')
        )

        log('Update {} location site(s)'.format(
            location_sites.count()
        ))

        signals.post_save.disconnect(
            location_site_post_save_handler
        )

        location_sites.update(
            site_code=F('legacy_site_code')
        )

        signals.post_save.connect(
            location_site_post_save_handler
        )
