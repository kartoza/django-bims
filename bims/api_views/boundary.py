# coding=utf-8
import json
from django.http.response import HttpResponse
from rest_framework.views import APIView
from bims.models.boundary import Boundary


class BoundaryList(APIView):
    """API for listing boundary."""

    def get(self, request, *args):
        boundaries = \
            Boundary.objects.filter().values(
                'id', 'name', 'type__level').order_by('type__level')
        return HttpResponse(json.dumps(list(boundaries)))
