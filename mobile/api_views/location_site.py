from django.contrib.gis.geos import Point, Polygon
from django.contrib.gis.measure import D
from django.contrib.gis.db.models.functions import Distance
from django.http import Http404
from rest_framework.response import Response
from rest_framework.views import APIView
from bims.models.location_site import LocationSite
from bims.serializers.location_site_serializer import (
    LocationSiteSerializer
)


class NearestLocationSites(APIView):
    def get(self, request, *args):
        lat = request.GET.get('lat', '')
        lon = request.GET.get('lon', '')
        radius = float(request.GET.get('radius', '100'))
        limit = int(request.GET.get('limit', '10'))
        extent = request.GET.get('extent', '')

        if not lat or not lon:
            if not extent:
                raise Http404()

        location_sites = LocationSite.objects.all()

        if extent:
            xmin, ymin, xmax, ymax = map(float, extent.split(','))
            bbox = Polygon.from_bbox((xmin, ymin, xmax, ymax))
            location_sites = location_sites.filter(
                geometry_point__within=bbox)
        else:
            point = Point(float(lon), float(lat))
            location_sites = location_sites.filter(
                geometry_point__distance_lte=(point, D(km=radius))
            ).annotate(
                distance=Distance('geometry_point', point)
            ).order_by('distance')

        return Response(
            LocationSiteSerializer(
                location_sites[:limit], many=True).data
        )
