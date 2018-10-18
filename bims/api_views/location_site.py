# coding=utf8
from django.contrib.gis.geos import Polygon
from django.db.models import Q
from django.http import Http404, HttpResponseBadRequest
from rest_framework.response import Response
from rest_framework.views import APIView
from bims.models.location_site import LocationSite
from bims.models.biological_collection_record import (
    BiologicalCollectionRecord
)
from bims.serializers.location_site_serializer import (
    LocationSiteSerializer,
    LocationSiteClusterSerializer
)
from bims.serializers.location_site_detail_serializer import \
    LocationSiteDetailSerializer
from bims.utils.cluster_point import (
    within_bbox,
    overlapping_area,
    update_min_bbox,
    geo_serializer
)
from bims.api_views.collection import GetCollectionAbstract


class LocationSiteList(APIView):
    """
    List all location site
    """

    def get(self, request, *args):
        location_site = LocationSite.objects.all()
        # get by bbox
        bbox = request.GET.get('bbox', None)
        if bbox:
            geom_bbox = Polygon.from_bbox(
                tuple([float(edge) for edge in bbox.split(',')]))
            location_site = location_site.filter(
                Q(geometry_point__intersects=geom_bbox) |
                Q(geometry_line__intersects=geom_bbox) |
                Q(geometry_polygon__intersects=geom_bbox) |
                Q(geometry_multipolygon__intersects=geom_bbox)
            )
        serializer = LocationSiteSerializer(location_site, many=True)
        return Response(serializer.data)


class LocationSiteDetail(APIView):
    """
    Return detail of location site
    """

    def get_object(self, pk):
        try:
            return LocationSite.objects.get(pk=pk)
        except LocationSite.DoesNotExist:
            raise Http404

    def get(self, request):
        site_id = request.GET.get('siteId')
        query_value = request.GET.get('search')
        filters = request.GET

        # Search collection
        collection_results, \
            site_results, \
            fuzzy_search = GetCollectionAbstract.apply_filter(
                query_value,
                filters,
                ignore_bbox=True)

        collection_ids = []
        if collection_results:
            collection_ids = list(collection_results.values_list(
                'model_pk',
                flat=True))
        context = {
            'collection_ids': collection_ids
        }
        location_site = self.get_object(site_id)
        serializer = LocationSiteDetailSerializer(
                location_site,
                context=context)
        return Response(serializer.data)


class LocationSiteClusterList(APIView):
    """
    List all location site in cluster
    """

    def clustering_process(
            self, records, zoom, pix_x, pix_y):
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
        """

        cluster_points = []
        for record in records:
            # get x,y of site
            centroid = record.get_centroid()
            if not centroid:
                continue
            x = centroid.x
            y = centroid.y

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
                serializer = LocationSiteClusterSerializer(
                    record)
                new_cluster = {
                    'count': 1,
                    'bbox': bbox,
                    'coordinates': [x, y],
                    'record': serializer.data
                }

                cluster_points.append(new_cluster)

        return cluster_points

    def get(self, request, *args):
        location_site = LocationSite.objects.all()
        # get by bbox
        zoom = request.GET.get('zoom', None)
        bbox = request.GET.get('bbox', None)
        icon_pixel_x = request.GET.get('icon_pixel_x', None)
        icon_pixel_y = request.GET.get('icon_pixel_y', None)

        if not zoom or not icon_pixel_x or not icon_pixel_y:
            return HttpResponseBadRequest(
                'zoom, icon_pixel_x, and icon_pixel_y need to be '
                'in parameters. '
                'zoom : zoom level of map. '
                'icon_pixel_x: size x of icon in pixel. '
                'icon_pixel_y: size y of icon in pixel. ')
        if bbox:
            geom_bbox = Polygon.from_bbox(
                tuple([float(edge) for edge in bbox.split(',')]))

            sites_ids = BiologicalCollectionRecord.objects.filter(
                validated=True).filter(
                Q(site__geometry_point__intersects=geom_bbox) |
                Q(site__geometry_line__intersects=geom_bbox) |
                Q(site__geometry_polygon__intersects=geom_bbox) |
                Q(site__geometry_multipolygon__intersects=geom_bbox)
            ).values('site').distinct()
            location_site = location_site.filter(
                id__in=sites_ids
            )
        cluster = self.clustering_process(
            location_site,
            int(float(zoom)),
            int(icon_pixel_x),
            int(icon_pixel_y)
        )
        return Response(geo_serializer(cluster)['features'])
