from django.core.management.base import BaseCommand
from django.db.models import Count, signals
from preferences import preferences
from bims.models import (
    LocationSite,
    location_site_post_save_handler
)
from bims.models.location_site import generate_site_code


class Command(BaseCommand):
    help = 'Fix duplicate site codes'

    def handle(self, *args, **options):
        dupe_sites = LocationSite.objects.values(
            'site_code'
        ).annotate(
            Count('id')
        ).order_by().filter(id__count__gt=1)

        signals.post_save.disconnect(
            location_site_post_save_handler,
            sender=LocationSite
        )

        print('Found {} dupes'.format(dupe_sites.count()))

        for dupe_site in dupe_sites:
            sites = LocationSite.objects.filter(
                site_code=dupe_site['site_code']
            ).exclude(
                biological_collection_record__source_collection=
                preferences.SiteSetting.site_code_generator)
            for site in sites:
                print('Updating {}'.format(site.id))
                site_code =  generate_site_code(
                    site,
                    site.latitude,
                    site.longitude
                )
                print(f'{dupe_site["site_code"]} -> {site_code}')
                if site_code:
                    site.site_code = site_code[0]
                    site.save()

        signals.post_save.connect(
            location_site_post_save_handler,
            sender=LocationSite
        )
