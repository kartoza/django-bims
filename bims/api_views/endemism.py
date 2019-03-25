# coding=utf-8
import json
from django.http.response import HttpResponse
from rest_framework.views import APIView
from bims.models.endemism import Endemism


class EndemismList(APIView):
    """API for listing all endemism"""

    def get(self, request, *args):
        endemism_list = Endemism.objects.filter(
            name__isnull=False
        ).values_list(
            'name', flat=True
        ).order_by(
            'name'
        )

        return HttpResponse(
            json.dumps(list(endemism_list)),
            content_type='application/json'
        )
