# coding=utf-8
from rest_framework.views import APIView
from rest_framework.response import Response
from bims_theme.models import ChartColor


class ChartColorsList(APIView):
    """Return list of chart colors"""

    def get(self, request, *args):
        colors = ChartColor.objects.all().values_list('color', flat=True)
        return Response(list(colors))
