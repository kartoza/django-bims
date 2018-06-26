# -*- coding: utf-8 -*-

import os
import json
from django.conf import settings
from django.core.management.base import BaseCommand
from bims.models.boundary import Boundary
from bims.models.boundary_type import BoundaryType
from bims.serializers.boundary_serializer import (
    BoundaryGeoSerializer
)


class Command(BaseCommand):
    help = 'Generate boundary geojson'

    def handle(self, *args, **options):
        for boundary_type in BoundaryType.objects.all():
            queryset = Boundary.objects.filter(type=boundary_type)
            geojson = BoundaryGeoSerializer(queryset, many=True).data
            directory = os.path.join(
                settings.MEDIA_ROOT,
                'geojson'
            )
            if not os.path.exists(directory):
                os.makedirs(directory)
            file_name = os.path.join(
                directory, '%s.geojson' % boundary_type.name
            )
            try:
                fd = open(file_name, 'w+')
                fd.write(json.dumps(geojson, separators=(',', ':')))
                fd.close()
            except IOError as e:
                print e
                pass
