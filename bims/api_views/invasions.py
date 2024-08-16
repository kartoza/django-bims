# coding=utf-8
import json
from django.http.response import HttpResponse
from rest_framework.views import APIView
from bims.models.invasion import Invasion


class InvasionsList(APIView):
    """API for listing all invasions"""

    def get(self, request, *args):
        invasions = Invasion.objects.values_list(
            'id', 'category', 'description'
        ).exclude(
            category__exact=''
        )

        invasions = list(invasions)

        return HttpResponse(
            json.dumps(list(dict.fromkeys(invasions))),
            content_type='application/json'
        )
