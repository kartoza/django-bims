# coding=utf8
from django.http import Http404
from rest_framework.response import Response
from rest_framework.views import APIView
from bims.models.boundary_type import BoundaryType
from bims.models.boundary import Boundary
from bims.serializers.boundary_serializer import BoundarySerializer


class ClusterList(APIView):
    """
    List of all cluster in a administrative_level
    """

    def get(self, request, administrative_level, format=None):
        try:
            boundary_type = BoundaryType.objects.get(
                name=administrative_level)
        except BoundaryType.DoesNotExist:
            raise Http404()

        boundaries = Boundary.objects.filter(
            type=boundary_type)
        serializer = BoundarySerializer(boundaries, many=True)
        return Response(serializer.data)
