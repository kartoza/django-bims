# -*- coding: utf-8 -*-

from abc import ABC
from django.contrib.gis.gdal import DataSource
from django.contrib.gis.geos import MultiPolygon, Polygon

from bims.models.boundary import Boundary
from bims.models.boundary_type import BoundaryType


class UpdateBoundary(ABC):
    help = 'Import countries from CSV file'

    def save_data(self, shapefile, boundary_type, column_name):
        """ Saving data boundary from shapefile.
        :param shapefile: shapefile data that hold boundaries data
        :type shapefile: str

        :param boundary_type: what boundary type that will be generated.
        :type boundary_type: str

        :param column_name: column name of boundary name
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
            # -------------------------------------------------
            # FINISH
            # -------------------------------------------------
            print('COPYING %s' % name)
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
            try:
                if 'MultiPolygon' not in geometry.geojson:
                    geometry = MultiPolygon(
                        [Polygon(coords) for coords in
                         boundary.geometry.coords[0]] +
                        [Polygon(geometry.coords[0])]).geojson
                else:
                    geometry = MultiPolygon(
                        [Polygon(coords) for coords in
                         boundary.geometry.coords[0]] +
                        [Polygon(coords) for coords in
                         geometry.coords[0]]).geojson
                    boundary.polygon_geometry = geometry
            except Exception:
                if 'MultiPolygon' not in geometry.geojson:
                    geometry = MultiPolygon(
                        Polygon(geometry.coords[0])).geojson
                else:
                    geometry = geometry.geojson
            boundary.geometry = geometry
            boundary.save()
