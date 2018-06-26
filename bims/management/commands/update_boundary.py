# -*- coding: utf-8 -*-

import logging
from django.contrib.gis.gdal import DataSource
from django.contrib.gis.geos import MultiPolygon, Polygon

from bims.models.boundary import Boundary
from bims.models.boundary_type import BoundaryType

logger = logging.getLogger(__name__)


class UpdateBoundary(object):
    """ Update boundaries from shapefile.
    Boundary that created based on boundary_type. E.g. Country
    And use column_name as indicator which column to be used
    for saving name of the boundary.

    """
    help = 'Import boundaries from shp file'

    def save_data(self, shapefile, boundary_type, column_name):
        """ Saving data boundary from shapefile.

        :param shapefile: shapefile path data that hold boundaries data
        :type shapefile: str

        :param boundary_type: what boundary type that will be generated.
        :type boundary_type: str

        :param column_name: column name of boundary name.
        Needed for naming the boundary.
        :type column_name: str
        """
        try:
            boundary_type = BoundaryType.objects.get(
                name=boundary_type)
        except BoundaryType.DoesNotExist:
            boundary_type = BoundaryType.objects.create(
                name=boundary_type
            )

        data_source = DataSource(
            shapefile)
        layer = data_source[0]
        for feature in layer:
            name = feature[column_name].value
            name = name.strip()

            print('COPYING %s' % name.encode('utf-8').strip())
            geometry = feature.geom
            try:
                boundary = Boundary.objects.get(
                    name=name,
                    type=boundary_type
                )
            except Boundary.DoesNotExist:
                boundary = Boundary.objects.create(
                    name=name,
                    type=boundary_type
                )
            if 'MultiPolygon' not in geometry.geojson:
                geometry = MultiPolygon(
                    Polygon(geometry.coords[0])).geojson
            else:
                geometry = geometry.geojson
            boundary.geometry = geometry
            boundary.save()
