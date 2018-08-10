# coding=utf8
from django.http import Http404
from rest_framework.response import Response
from rest_framework.views import APIView
from bims.models.location_type import LocationType


class LocationTypeAllowedGeometryDetail(APIView):
    """
    Return allowed geometry of location site
    """

    def get_object(self, pk):
        try:
            return LocationType.objects.get(pk=pk)
        except LocationType.DoesNotExist:
            raise Http404

    def get(self, request, pk, format=None):
        location_site = self.get_object(pk)
        return Response(location_site.allowed_geometry)
