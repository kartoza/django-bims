# -*- coding: utf-8 -*-
import os
import csv
from django.core.management.base import BaseCommand
from django.contrib.gis.geos import Point
from django.db.models import signals
from bims.models import LocationSite, location_site_post_save_handler


class Command(BaseCommand):
    """
    Read coordinates from Rivers.Database.Corrected.Site.csv,
    update site coordinate based on site code
    """
    help = "Fix river site coordinates"

    def handle(self, *args, **options):
        signals.post_save.disconnect(
            location_site_post_save_handler,
        )
        filename = 'Rivers.Database.Corrected.Site.csv'
        folder_name = 'data'
        file_path = os.path.join(
            os.path.abspath(os.path.dirname(__name__)),
            'bims/static/{folder}/{filename}'.format(
                folder=folder_name,
                filename=filename
            ))
        with open(file_path) as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=',')
            line_count = 0
            for row in csv_reader:
                print('Processing %s' % line_count)
                line_count += 1
                if line_count - 1 == 0:
                    continue
                site_code = row[0]
                lat = row[1]
                lon = row[2]
                sites = LocationSite.objects.filter(
                    site_code__icontains=site_code
                )
                site_point = Point(
                    float(lon),
                    float(lat))

                if sites:
                    for site in sites:
                        print('Updating %s' % site.site_code)
                        site.geometry_point = site_point
                        site.save()

            print('Processed %s lines.' % line_count)
            signals.post_save.connect(
                location_site_post_save_handler,
            )
