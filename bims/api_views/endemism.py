# coding=utf-8
import json
from django.http.response import HttpResponse
from rest_framework.views import APIView
from bims.models.endemism import Endemism


class EndemismList(APIView):
    """API for listing all endemism"""

    def get(self, request, *args):
        endemism_list = Endemism.objects.filter(
            name__isnull=False,
        ).order_by('display_order').values_list(
            'name', 'description'
        ).exclude(
            name__exact=''
        )

        endemism_list = list(endemism_list)

        if 'Unknown' not in [end[0] for end in endemism_list]:
            endemism_list.append(('Unknown', 'Endemism is unknown'))

        return HttpResponse(
            json.dumps(list(dict.fromkeys(endemism_list))),
            content_type='application/json'
        )
