# coding=utf8

from django.http import HttpResponseBadRequest
import math
from rest_framework.response import Response
from rest_framework.views import APIView
from haystack.query import SearchQuerySet
from bims.models.biological_collection_record import \
    BiologicalCollectionRecord
from bims.models.location_site import LocationSite
from bims.serializers.bio_collection_record_doc_serializer import \
    BiologicalCollectionRecordDocSerializer
from bims.serializers.location_type_serializer import \
    LocationTypeSerializer


class ClusterModuleList(APIView):
    """
    List of all cluster in module group
    """

    def update_min_bbox(self, point, min_bbox):
        """
        For every cluster we are calculating minimum bbox for point in the
        cluster
        This is required in order to have nicer click to zoom map behaviour
        (fitBounds)
        This minimum bbox is used for calculating the clustering of points for
        the next point.

        :param point: point that will be used for creating new minimum bbox
        :type point: tuple

        :param min_bbox: old minimum bbox that will be updated.
        :type min_bbox: tuple

        :return new_min_bbox: new minimum bbox.
        :rtype new_min_bbox: tuple
        """

        new_min_bbox = list(min_bbox)

        if point[0] < min_bbox[0]:
            new_min_bbox[0] = point[0]
        if point[0] > min_bbox[2]:
            new_min_bbox[2] = point[0]
        if point[1] < min_bbox[1]:
            new_min_bbox[1] = point[1]
        if point[1] > min_bbox[3]:
            new_min_bbox[3] = point[1]

        return new_min_bbox

    def within_bbox(self, point, bbox):
        """
        Check if a point (x, y) is within a bbox (minx, miny, maxx, maxy)

        :param point: point that will be checked.
        :type point: tuple

        :param bbox: bbox that will be used for checking point is within bbox.
        :type bbox: tuple

        :return: is point within bbox or not
        :rtype: bool
        """

        if bbox[0] < point[0] < bbox[2] and bbox[1] < point[1] < bbox[3]:
            return True
        else:
            return False

    def get_center_of_bbox(self, bbox):
        """
        Get center of bbox

        :param bbox: bbox.
        :type bbox: tuple

        :return: point of center of bbox
        :rtype: list
        """
        return (((bbox[2] - bbox[0]) / 2) + bbox[0], bbox[1])

    def overlapping_area(self, zoom, pix_x, pix_y, lat):
        """
        Calculate an area (lng_deg, lat_deg) in degrees for an icon and a zoom
        Since we are using a World Mercator projection deformation is uniform in
        all directions and depends only on latitude

        :param zoom: zoom level of map
        :type zoom: int

        :param pix_x: pixel x of icon
        :type pix_x: int

        :param pix_y: pixel y of icon
        :type pix_y: int
        """
        C = (2 * 6378137.0 * math.pi) / 256.  # one pixel
        C2 = (2 * 6378137.0 * math.pi) / 360.  # one degree

        lat_deformation = (C * math.cos(math.radians(lat)) / 2 ** zoom)

        lat_deg = (lat_deformation * pix_y) / C2
        lng_deg = (lat_deformation * pix_x) / C2

        return (lng_deg, lat_deg)

    def clustering_process(
            self, records, zoom, pix_x, pix_y, SERIALIZER, module=None, mapbbox=None):
        """
        Iterate records and create point clusters
        We use a simple method that for every point, that is not within any
        cluster, calculate it's 'catchment' area and add it to the cluster
        If a point is within a cluster 'catchment' area increase point count for
        that cluster and recalculate clusters minimum bbox

        :param records: list of records.
        :type records: list

        :param zoom: zoom level of map
        :type zoom: int

        :param pix_x: pixel x of icon
        :type pix_x: int

        :param pix_y: pixel y of icon
        :type pix_y: int

        :param SERIALIZER: SERIALIZER to be used for this clustering

        :param module: filter records by module
        :type module: str

        :param mapbbox: filter records by current mapbbox
        :type mapbbox: tuple
        """

        cluster_points = []
        for record in records:
            # get actual object from elasticsearch query
            record = record.object
            # get x,y of site
            x = record.site.geometry_point.x
            y = record.site.geometry_point.y

            if module and module != 'location_site':
                result_module = record.get_children()._meta.verbose_name
                if result_module != module:
                    continue

            if mapbbox:
                if not self.within_bbox((x, y), mapbbox):
                    continue

            # check every point in cluster_points
            for pt in cluster_points:
                if 'minbbox' not in pt:
                    pt['minbbox'] = pt['bbox']

                if self.within_bbox((x, y), pt['minbbox']):
                    # it's in the cluster 'catchment' area
                    pt['count'] += 1
                    pt['minbbox'] = self.update_min_bbox(
                        (x, y), pt['minbbox'])
                    break

            else:
                # point is not in the catchment area of any cluster
                x_range, y_range = self.overlapping_area(
                    zoom, pix_x, pix_y, y)
                bbox = (
                    x - x_range * 1.5, y - y_range * 1.5,
                    x + x_range * 1.5, y + y_range * 1.5
                )
                serializer = SERIALIZER(
                    record)
                new_cluster = {
                    'count': 1,
                    'bbox': bbox,
                    'coordinates': [x, y],
                    'record': serializer.data
                }

                cluster_points.append(new_cluster)

        return cluster_points

    def geo_serializer(self, records):
        """
        Return geojson of records with clean dictionary.

        :param records: raw records
        :type records: list

        :return: geojson records
        :rtype: dict
        """
        geojson = {
            "type": "FeatureCollection",
            "features": []
        }

        for record in records:
            if record['count'] == 1:
                geojson['features'].append(
                    {
                        "geometry": {
                            "type": "Point",
                            "coordinates": record['coordinates']
                        },
                        "type": "Feature",
                        "properties": record['record']
                    }
                )
            else:
                geojson['features'].append(
                    {
                        "geometry": {
                            "type": "Point",
                            "coordinates": self.get_center_of_bbox(
                                record['minbbox']
                            )
                        },
                        "type": "Feature",
                        "properties": {
                            'count': record['count']
                        }
                    }
                )
        return geojson

    def get(self, request, format=None):
        sqs = SearchQuerySet()
        zoom = request.GET.get('zoom', None)
        icon_pixel_x = request.GET.get('icon_pixel_x', None)
        icon_pixel_y = request.GET.get('icon_pixel_y', None)

        if not zoom or not icon_pixel_x or not icon_pixel_y:
            return HttpResponseBadRequest(
                'zoom, icon_pixel_x, and icon_pixel_y need to be '
                'in parameters. '
                'zoom : zoom level of map. '
                'icon_pixel_x: size x of icon in pixel. '
                'icon_pixel_y: size y of icon in pixel. ')

        results = []
        # get records by query
        query_value = request.GET.get('query', '')
        bbox = request.GET.get('bbox', None)
        module_filters = request.GET.get('module', 'location_site')

        if module_filters != 'location_site':
            if query_value:
                clean_query = sqs.query.clean(query_value)
                # TODO : Need OR in here or there will be duplicated records
                sqs = sqs.filter(
                    original_species_name=clean_query
                )
                # results.extend(
                #     sqs.filter(
                #         collector=clean_query
                #     ).models(BiologicalCollectionRecord)
                # )
            results.extend(
                sqs.models(BiologicalCollectionRecord)
            )
            SERIALIZER = BiologicalCollectionRecordDocSerializer

        else:
            if query_value:
                clean_query = sqs.query.clean(query_value)
                sqs = sqs.filter(
                    name=clean_query
                )
            results.extend(
                sqs.models(LocationSite)
            )
            SERIALIZER = LocationTypeSerializer

        cluster = self.clustering_process(
            results, int(zoom), int(icon_pixel_x), int(icon_pixel_y),
            SERIALIZER,
            module_filters, tuple([float(edge) for edge in bbox.split(',')]))
        return Response(self.geo_serializer(cluster))
