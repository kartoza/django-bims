# coding=utf-8
import requests
import json

from bims.utils.get_key import get_key
from django.http import Http404
from braces.views import LoginRequiredMixin
from rest_framework.views import APIView, Response
from rest_framework import status


class SiteInCountry(LoginRequiredMixin, APIView):
    """
    Check if site is inside base country
    """
    def get(self, request):
        lat = request.GET.get('lat', None)
        lon = request.GET.get('lon', None)

        if not lat or not lon:
            raise Http404('Missing coordinates')
        url = (
            '{base_url}/api/v2/query?registry=service&key=combination_saprovince_sadc_boundary&'
            'x={lon}&y={lat}&outformat=json'
        ).format(
            base_url=get_key('GEOCONTEXT_URL'),
            lon=lon,
            lat=lat
        )

        try:
            response = requests.get(url)
            if response.status_code == 200:
                province = json.loads(response.content)
                if province['value'] is not None:
                    return Response(True)
                return Response(False)

        except Exception as e:  # noqa
            pass

        return Response({
            'data': 'Site is not in the country'},
            status=status.HTTP_404_NOT_FOUND)
