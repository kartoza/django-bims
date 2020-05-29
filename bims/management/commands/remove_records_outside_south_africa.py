# -*- coding: utf-8 -*-
import os
import json
from django.conf import settings
from django.contrib.gis.geos import GEOSGeometry
from django.core.management.base import BaseCommand
from django.db.models import signals
from bims.models import (
    Boundary,
    BiologicalCollectionRecord,
    SearchProcess,
    collection_post_save_handler
)


class Command(BaseCommand):
    help = 'Remove records outside South Africa'

    def all_boundaries(self, parents):
        """
        Returns all children boundaries
        :param parents: list of parents
        :return: list boundaries
        """
        boundaries = Boundary.objects.filter(
            top_level_boundary__in=parents
        )
        if not boundaries:
            return boundaries
        else:
            return boundaries | self.all_boundaries(boundaries)

    def handle(self, *args, **options):
        json_data = open(
            os.path.join(settings.MEDIA_ROOT, 'south-africa.geojson'))
        data1 = json.load(json_data)
        polygon_union = None
        for feature in data1['features']:
            multipolygon = GEOSGeometry(json.dumps(feature['geometry']))
            if not polygon_union:
                polygon_union = multipolygon
            else:
                polygon_union = polygon_union.union(multipolygon)

        print('Get all records outside SA')
        bio = BiologicalCollectionRecord.objects.filter(
            source_collection='gbif'
        ).exclude(
            site__geometry_point__within=polygon_union
        )
        print('Got %s records' % bio.count())
        bio.delete()
        SearchProcess.objects.all().delete()
        signals.post_save.connect(
            collection_post_save_handler
        )
