# coding=utf-8
import json
from django.http.response import HttpResponse
from rest_framework.response import Response
from rest_framework.views import APIView
from bims.models.boundary import Boundary
from bims.serializers.boundary_serializer import (
    BoundaryGeojsonSerializer
)


class BoundaryList(APIView):
    """API for listing boundary."""

    def get(self, request, *args):
        boundaries = \
            Boundary.objects.exclude(type__level=1).filter().values(
                'id', 'name', 'type__name',
                'top_level_boundary', 'type__level'
            ).order_by('type__level', 'name')
        return HttpResponse(json.dumps(list(boundaries)))


class BoundaryGeojson(APIView):
    """API for returning boundary geojson."""

    def get(self, request, *args):
        ids = request.GET.get('ids', [])
        ids = json.loads(ids)
        boundaries = \
            Boundary.objects.filter(type__level=4).filter(
                id__in=ids)
        return Response(BoundaryGeojsonSerializer(boundaries, many=True).data)
