# -*- coding: utf-8 -*-
import os
import ast
import json
from django.conf import settings
from django.contrib.gis.geos import GEOSGeometry
from django.core.management.base import BaseCommand
from bims.models import (
    BiologicalCollectionRecord,
    LocationSite,
    Survey
)


class Command(BaseCommand):
    help = 'Remove records outside boundary'

    def add_arguments(self, parser):
        parser.add_argument(
            '-bf',
            '--boundary-file',
            dest='boundary_file',
            default='',
            help='Geojson file name of the boundary'
        )
        parser.add_argument(
            '-log',
            '--log-only',
            dest='log_only',
            default='False',
            help='Only show the log, dont delete the records'
        )

    def handle(self, *args, **options):
        boundary_file = options.get('boundary_file', '')
        log_only = ast.literal_eval(options.get('log_only', 'False'))
        json_data = open(os.path.join(settings.MEDIA_ROOT, boundary_file))
        data1 = json.load(json_data)
        polygon_union = None
        for feature in data1['features']:
            multipolygon = GEOSGeometry(json.dumps(feature['geometry']))
            if not polygon_union:
                polygon_union = multipolygon
            else:
                polygon_union = polygon_union.union(multipolygon)

        print('Getting the records...')
        bio = BiologicalCollectionRecord.objects.exclude(
            site__geometry_point__within=polygon_union
        )
        bio_ids = list(bio.values_list('id', flat=True))
        sites = LocationSite.objects.filter(
            biological_collection_record__in=bio_ids
        ).distinct()
        surveys = Survey.objects.filter(
            biological_collection_record__in=bio_ids
        ).distinct()

        print('Got %s records' % bio.count())
        print('Got %s sites' % sites.count())
        print('Got %s surveys' % surveys.count())

        if not log_only:
            print('Deleting the records...')
            surveys.delete()
            bio.delete()
            sites.delete()
