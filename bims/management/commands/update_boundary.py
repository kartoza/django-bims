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

    def is_ascii(self, s):
        return all(ord(c) < 128 for c in s)

    def save_data(
            self, shapefile, boundary_type, column_name, column_code_name,
            boundary_level, column_top_boundary=None):
        """ Saving data boundary from shapefile.

        :param shapefile: shapefile path data that hold boundaries data
        :type shapefile: str

        :param boundary_type: what boundary type that will be generated.
        :type boundary_type: str

        :param column_name: column name of boundary name.
        Needed for naming the boundary.
        :type column_name: str

        :param column_code_name: column name of boundary code name.
        Needed for code name of the boundary.
        :type column_code_name: str

        :param boundary_level: Level of boundary in administrative.
        :type boundary_level: int

        :param column_top_boundary: column name of top of boundary.
        It is used for getting which boundary that in top of this boundary.
        It is codename of that boundary
        :type column_top_boundary: str
        """
        try:
            boundary_type = BoundaryType.objects.get(
                name=boundary_type)
        except BoundaryType.DoesNotExist:
            boundary_type = BoundaryType.objects.create(
                name=boundary_type
            )
        boundary_type.level = boundary_level
        boundary_type.save()

        Boundary.objects.filter(type=boundary_type).delete()

        data_source = DataSource(
            shapefile)
        layer = data_source[0]
        for feature in layer:
            name = feature[column_name].value

            # TODO :Fix grapelli that can't handle non ascii
            if not self.is_ascii(name):
                continue

            name = name.encode('utf-8').strip()

            codename = feature[column_code_name].value
            codename = codename.strip()

            print('COPYING %s' % name)

            # get top boundary
            top_level_boundary = None
            if column_top_boundary:
                top_boundary_codename = feature[
                    column_top_boundary].value
                top_boundary_codename = top_boundary_codename.strip()

                try:
                    top_level = (boundary_level - 1)
                    boundary = Boundary.objects.get(
                        code_name=top_boundary_codename,
                        type__level=top_level
                    )
                    top_level_boundary = boundary
                except Boundary.DoesNotExist:
                    print('Top boundary=%s not found' %
                          top_boundary_codename)

            boundary = Boundary.objects.create(
                name=name,
                type=boundary_type,
                code_name=codename,
                top_level_boundary=top_level_boundary
            )
            geometry = feature.geom
            if 'MultiPolygon' not in geometry.geojson:
                geometry = MultiPolygon(
                    Polygon(geometry.coords[0])).geojson
            else:
                geometry = geometry.geojson
            boundary.geometry = geometry
            boundary.save()
