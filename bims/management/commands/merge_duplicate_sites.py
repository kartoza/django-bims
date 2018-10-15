# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand
from bims.models import LocationSite, BiologicalCollectionRecord


class Command(BaseCommand):
    help = 'Merge duplicate sites'

    def handle(self, *args, **options):
        all_sites = LocationSite.objects.all()
        deleted_sites = []

        for site in all_sites:
            if site.id in deleted_sites:
                continue
            location_sites = LocationSite.objects.filter(
                location_type=site.location_type,
                geometry_point=site.geometry_point,
                name=site.name
            ).exclude(id=site.id)

            if len(location_sites) > 0:
                for location_site in location_sites:
                    if location_site.id not in deleted_sites:
                        BiologicalCollectionRecord.objects.filter(
                            site=location_site
                        ).update(
                            site=site
                        )
                        deleted_sites.append(location_site.id)
                        location_site.delete()
