# coding=utf-8
import json
from django.http.response import HttpResponse
from rest_framework.views import APIView
from bims.utils.river_catchments import get_river_catchment_tree


class RiverCatchmentList(APIView):
    """API for listing all endemism"""

    def get(self, request, *args):
        river_catchment_data = get_river_catchment_tree()

        return HttpResponse(
            json.dumps(list(river_catchment_data)),
            content_type='application/json'
        )
