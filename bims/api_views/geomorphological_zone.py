# coding=utf-8
import json

import requests
from requests.exceptions import HTTPError
from braces.views import LoginRequiredMixin
from rest_framework.views import APIView, Response

from bims.utils.get_key import get_key


class GetGeomorphologicalZone(LoginRequiredMixin, APIView):

    def get(self, request):
        lat = request.GET.get('lat', None)
        lon = request.GET.get('lon', None)
        geomorphological_group = {}
        geomorphological_zone = ''

        url = (
            '{base_url}/api/v2/query?registry=group&key=geomorphological_group&'
            'x={lon}&y={lat}&outformat=json'
        ).format(
            base_url=get_key('GEOCONTEXT_URL'),
            lon=lon,
            lat=lat
        )
        try:
            response = requests.get(url)
            if response.status_code == 200:
                geomorphological_group = json.loads(response.content)
                if 'services' in geomorphological_group:
                    if 'service_registry_values' not in geomorphological_group:
                        geomorphological_group['service_registry_values'] = (
                            geomorphological_group['services']
                        )
                geomorphological_zone = (
                    geomorphological_group['services'][1]['value']
                )
        except (HTTPError, ValueError, KeyError):
            pass

        return Response({
            'geomorphological_group': geomorphological_group,
            'geomorphological_zone': geomorphological_zone,
        })
