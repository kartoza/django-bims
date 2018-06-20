# coding=utf8

from django.http import HttpResponseBadRequest, Http404
from rest_framework.response import Response
from rest_framework.views import APIView
from bims.models.biological_collection_record import \
    BiologicalCollectionRecord
from bims.serializers.bio_collection_record_doc_serializer import \
    BiologicalCollectionRecordDocSerializer
from bims.utils.cluster_point import (
    within_bbox,
    overlapping_area,
    update_min_bbox,
    geo_serializer
)


class ClusterTaxaList(APIView):
    """
    List of all cluster in module group
    """

    def clustering_process(
            self, records, zoom, pix_x, pix_y,
            SERIALIZER, mapbbox=None):
        """
        Iterate records and create point clusters
        We use a simple method that for every point, that is not within any
        cluster, calculate it's 'catchment' area and add it to the cluster
        If a point is within a cluster 'catchment' area increase point
        count for that cluster and recalculate clusters minimum bbox

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
            # get x,y of site
            x = record.site.geometry_point.x
            y = record.site.geometry_point.y

            if mapbbox:
                if not within_bbox((x, y), mapbbox):
                    continue

            # check every point in cluster_points
            for pt in cluster_points:
                if 'minbbox' not in pt:
                    pt['minbbox'] = pt['bbox']

                if within_bbox((x, y), pt['minbbox']):
                    # it's in the cluster 'catchment' area
                    pt['count'] += 1
                    pt['minbbox'] = update_min_bbox(
                        (x, y), pt['minbbox'])
                    break

            else:
                # point is not in the catchment area of any cluster
                x_range, y_range = overlapping_area(
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

    def get(self, request, pk, format=None):
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

        try:
            record = BiologicalCollectionRecord.objects.get(pk=pk)
        except BiologicalCollectionRecord.DoesNotExist:
            raise Http404
        # get records by query
        bbox = request.GET.get('bbox', None)

        queryset = BiologicalCollectionRecord.objects.filter(
            taxon_gbif_id=record.taxon_gbif_id
        )

        cluster = self.clustering_process(
            queryset, int(zoom), int(icon_pixel_x), int(icon_pixel_y),
            BiologicalCollectionRecordDocSerializer,
            tuple([float(edge) for edge in bbox.split(',')]))
        return Response(geo_serializer(cluster))
