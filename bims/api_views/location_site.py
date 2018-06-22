# coding=utf8
from django.contrib.gis.geos import Polygon
from django.db.models import Q
from django.http import Http404
from rest_framework.response import Response
from rest_framework.views import APIView
from bims.models.location_site import LocationSite
from bims.serializers.location_site_serializer import LocationSiteSerializer
from bims.serializers.location_site_detail_serializer import \
    LocationSiteDetailSerializer


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

    def get(self, request, pk, format=None):
        location_site = self.get_object(pk)
        serializer = LocationSiteDetailSerializer(location_site)
        return Response(serializer.data)
