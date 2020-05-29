# -*- coding: utf-8 -*-
import os
import json
import csv
from django.conf import settings
from django.contrib.gis.geos import GEOSGeometry
from django.contrib.gis.geos import fromfile
from django.core.management.base import BaseCommand
from bims.models import (
    Boundary,
    LocationSite,
)


class Command(BaseCommand):
    help = 'Get sites outside SA'


    def handle(self, *args, **options):
        json_data = open(os.path.join(settings.MEDIA_ROOT, 'south-africa.geojson'))
        data1 = json.load(json_data)
        polygon_union = None
        for feature in data1['features']:
            multipolygon = GEOSGeometry(json.dumps(feature['geometry']))
            if not polygon_union:
                polygon_union = multipolygon
            else:
                polygon_union = polygon_union.union(multipolygon)

        print('Get all records outside SA')
        sites = LocationSite.objects.exclude(
            geometry_point__within=polygon_union
        ).exclude(
            biological_collection_record__isnull=True
        ).distinct('id')

        csv_path = os.path.join(settings.MEDIA_ROOT, 'sites')
        if not os.path.exists(csv_path): os.mkdir(csv_path)
        csv_file_path = os.path.join(csv_path, '{t}.csv'.format(
            t='sites_list'
        ))

        with open(csv_file_path, mode='w') as csv_file:
            writer = csv.writer(
                csv_file, delimiter=',', quotechar='"',
                quoting=csv.QUOTE_MINIMAL)
            writer.writerow([
                'Site Code', 'Original Site Code', 'Lat', 'Lon', 'Link'])
            for site in sites:
                print(site)
                csv_data = []

                csv_data.append(site.site_code.encode('utf-8'))
                csv_data.append(site.legacy_site_code.encode('utf-8'))
                csv_data.append(site.latitude)
                csv_data.append(site.longitude)
                csv_data.append('http://staging.freshwaterbiodiversity.org/location-site-form/update/?id={}'.format(site.id))

                writer.writerow(csv_data)
