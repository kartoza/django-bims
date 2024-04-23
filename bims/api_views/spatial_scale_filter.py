# coding=utf-8
from django.core.cache import cache
from rest_framework.views import APIView, Response
from bims.tasks.location_context import generate_spatial_scale_filter, get_spatial_scale_filter


class SpatialScaleFilterList(APIView):
    """API for listing all spatial scale filter"""

    def get(self, request, *args):
        spatial_scale_filter = get_spatial_scale_filter(request)
        if not spatial_scale_filter:
            groups = []
        else:
            groups = spatial_scale_filter

        return Response(
            groups
        )
