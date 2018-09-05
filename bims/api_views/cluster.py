# coding=utf8
from rest_framework.response import Response
from rest_framework.views import APIView
from bims.models.cluster import Cluster
from bims.models.boundary_type import BoundaryType
from bims.models.boundary import Boundary
from bims.serializers.boundary_serializer import BoundaryClusterSerializer


class ClusterList(APIView):
    """
    List of all cluster in a administrative_level
    """

    def get(self, request, administrative_level, format=None):
        clusters = Cluster.objects.filter(
            boundary__type__name=administrative_level,
            module='location site',
            site_count__gt=0)
        serializer = BoundaryClusterSerializer(clusters, many=True)
        return Response(serializer.data)
