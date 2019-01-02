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

    def get_boundary_tree(self, parent=None):
        boundaries_dict = []
        if parent:
            boundaries = Boundary.objects.filter(
                top_level_boundary=parent
            )
        else:
            boundaries = Boundary.objects.filter(
                top_level_boundary__isnull=True
            )
        for boundary in boundaries:
            boundaries_dict.append({
                'key': boundary.name,
                'value': boundary.id,
                'children': self.get_boundary_tree(boundary)
            })

        return boundaries_dict

    def get(self, request, *args):
        try:
            boundary_parent = Boundary.objects.get(type__level=1)
        except (Boundary.DoesNotExist, Boundary.MultipleObjectsReturned):
            boundary_parent = None
        boundaries = self.get_boundary_tree(boundary_parent)
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
