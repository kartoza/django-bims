import os
import csv
from django.core.management.base import BaseCommand
from django.conf import settings
from django.db.models import signals
from bims.utils.logger import log
from bims.models.location_site import (
    LocationSite, location_site_post_save_handler
)

LATITUDE = 'Latitude'
LONGITUDE = 'Longitude'
CORRECTED_LATITUDE = 'Corrected Latitude'
CORRECTED_LONGITUDE = 'Corrected Longitude'
USER_SITE_CODE = 'User Site Code'
REFINED_GEO_ZONE = 'Refined Geomorphological Zone'
USER_RIVER_NAME = 'User River Name'
FBIS_SITE_CODE = 'FBIS Site Code'


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument(
            '-file',
            '--csv-file',
            dest='csv_file',
            default=None,
            help='CSV file for updating sites data'
        )

    def handle(self, *args, **options):
        csv_file_name = options.get('csv_file', None)
        csv_file_path = os.path.join(
            settings.MEDIA_ROOT,
            csv_file_name
        )

        if not csv_file_name or not os.path.exists(csv_file_path):
            log('Csv file name not provided / csv file does not exist')
            return False

        # Disconnect all related signals
        signals.post_save.disconnect(
            location_site_post_save_handler
        )

        not_updated = []

        with open(csv_file_path) as csv_file:
            csv_reader = csv.DictReader(csv_file)
            for row in csv_reader:
                # Search LocationSite with the same original latitude and longitude
                if USER_SITE_CODE in row:
                    location_sites = LocationSite.objects.filter(
                        legacy_site_code=row[USER_SITE_CODE]
                    )
                    site_code = USER_SITE_CODE
                elif FBIS_SITE_CODE in row:
                    location_sites = LocationSite.objects.filter(
                        site_code=row[FBIS_SITE_CODE]
                    )
                    site_code = FBIS_SITE_CODE
                else:
                    not_updated.append(row[site_code])
                    continue
                if location_sites.count() > 0:
                    location_site = location_sites[0]
                    location_site.legacy_river_name = row[USER_RIVER_NAME]

                    if REFINED_GEO_ZONE in row:
                        location_site.refined_geomorphological = row[REFINED_GEO_ZONE]

                    if CORRECTED_LATITUDE in row and CORRECTED_LONGITUDE in row:
                        try:
                            updated_latitude = float(row[CORRECTED_LATITUDE])
                            updated_longitude = float(row[CORRECTED_LONGITUDE])
                        except ValueError:
                            not_updated.append(row[site_code])
                            continue
                        if (
                            location_site.latitude != updated_latitude or
                            location_site.longitude != updated_longitude):
                            location_site.latitude = updated_latitude
                            location_site.longitude = updated_longitude
                            log('Lat lon updated')
                    location_site.save()
                    log('Location site {} updated'.format(
                        row[site_code]))
                else:
                    not_updated.append(row[site_code])

        log('Not updated : {}'.format(','.join(not_updated)))
        # Reconnect signals
        signals.post_save.connect(
            location_site_post_save_handler
        )
