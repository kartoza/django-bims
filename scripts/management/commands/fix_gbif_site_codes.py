from django.core.management import BaseCommand
from django.db.models import signals
from bims.models import (
    LocationSite, location_site_post_save_handler, generate_site_code,
    location_context_post_save_handler, LocationContextGroup,
    LocationContextFilter, LocationContextFilterGroupOrder
)
from bims.utils.logger import log
from bims.location_site.river import (
    fetch_river_name
)


class Command(BaseCommand):
    # Update location sites to use
    # legacy site codes if they have correct format

    def handle(self, *args, **options):
        location_sites = LocationSite.objects.exclude(
            site_code__iregex=r'([A-Za-z0-9]){1,6}-([A-Za-z0-9]*)$'
        ).filter(
            biological_collection_record__source_collection='gbif'
        ).distinct()

        log('Update {} location site(s)'.format(
            location_sites.count()
        ))

        signals.post_save.disconnect(
            location_site_post_save_handler
        )
        signals.post_save.disconnect(
            location_context_post_save_handler,
            sender=LocationContextGroup
        )
        signals.post_save.disconnect(
            location_context_post_save_handler,
            sender=LocationContextFilter
        )
        signals.post_save.disconnect(
            location_context_post_save_handler,
            sender=LocationContextFilterGroupOrder
        )

        index = 0
        for location_site in location_sites:
            log('processing %s of %s' % (
                index,
                location_sites.count()
            ))
            index += 1
            lat = location_site.geometry_point[1]
            lon = location_site.geometry_point[0]
            site_code, catchment = generate_site_code(
                location_site=location_site,
                lat=lat,
                lon=lon
            )
            log('New site code %s' % (
                site_code
            ))
            location_site.site_code = site_code
            location_site.save()

        signals.post_save.connect(
            location_site_post_save_handler
        )
        signals.post_save.connect(
            location_context_post_save_handler,
            sender=LocationContextGroup
        )
        signals.post_save.connect(
            location_context_post_save_handler,
            sender=LocationContextFilter
        )
        signals.post_save.connect(
            location_context_post_save_handler,
            sender=LocationContextFilterGroupOrder
        )
