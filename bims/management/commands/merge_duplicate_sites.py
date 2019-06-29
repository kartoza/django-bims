from django.core.management.base import BaseCommand
from django.db.models import Count
from bims.models import (
    LocationSite,
    BiologicalCollectionRecord
)


class Command(BaseCommand):
    help = 'Merge duplicate sites'

    def handle(self, *args, **options):
        dupe_sites = LocationSite.objects.values(
            'latitude',
            'longitude',
            'site_code'
        ).annotate(
            Count('id')
        ).order_by().filter(id__count__gt=1)
        for dupe_site in dupe_sites:
            sites = LocationSite.objects.filter(
                latitude=dupe_site['latitude'],
                longitude=dupe_site['longitude']
            )
            site_destination = None
            all_collections = []
            for site in sites:
                if not site_destination:
                    site_destination = site
                else:
                    if len(site.site_description) > len(
                            site_destination.site_description):
                        site_destination = site
                all_collections.append(
                    BiologicalCollectionRecord.objects.filter(
                        site=site
                    )
                )
            for collections in all_collections:
                collections.update(site=site_destination)
            for site in sites:
                if site != site_destination:
                    site.delete()
            print(sites.count())
