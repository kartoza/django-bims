# coding=utf-8
import json
from django.http.response import HttpResponse
from rest_framework.views import APIView
from bims.models.endemism import Endemism


class EndemismList(APIView):
    """API for listing all endemism"""

    def get(self, request, *args):
        endemisms = Endemism.objects.all().values_list(
            'name', flat=True
        )

        return HttpResponse(
            json.dumps(list(endemisms)),
            content_type='application/json'
        )
