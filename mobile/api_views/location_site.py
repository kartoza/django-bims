from django.contrib.gis.geos import Point
from django.contrib.gis.measure import D
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
        radius = float(request.GET.get('radius', '10'))
        limit = int(request.GET.get('limit', '10'))

        if not lat or not lon:
            raise Http404()

        point = Point(float(lon), float(lat))

        location_sites = LocationSite.objects.filter(
            geometry_point__distance_lte=(point, D(km=radius))
        )[:limit]
        return Response(
            LocationSiteSerializer(location_sites, many=True).data
        )
