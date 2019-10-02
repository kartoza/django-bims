# coding=utf-8
import os
import json
from django.conf import settings
from rest_framework.views import APIView, Response
from bims.tasks.location_context import generate_spatial_scale_filter


class SpatialScaleFilterList(APIView):
    """API for listing all spatial scale filter"""

    def get(self, request, *args):
        file_name = 'spatial_scale_filter_list.txt'
        file_path = os.path.join(
            settings.MEDIA_ROOT,
            file_name
        )
        if not os.path.exists(file_path):
            groups = []
            generate_spatial_scale_filter.delay(file_path)
        else:
            with open(file_path, 'r') as file_handle:
                groups = json.load(file_handle)

        return Response(
            groups
        )
