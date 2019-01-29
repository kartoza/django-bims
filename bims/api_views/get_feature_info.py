import re
import requests
from requests.exceptions import HTTPError, ConnectionError
from django.http import HttpResponse
from rest_framework.views import APIView
from rest_framework.authentication import BasicAuthentication
from bims.permissions.auth_class import CsrfExemptSessionAuthentication


class GetFeatureInfo(APIView):
    """Request GetFeatureInfo from geoserver"""
    authentication_classes = (CsrfExemptSessionAuthentication,
                              BasicAuthentication)

    def remove_proxy(self, url):
        return re.sub(r'(/?)bims_proxy(/?)|', '', url)

    def post(self, request):
        layer_source = request.POST.get('layerSource', None)
        layer_source = self.remove_proxy(layer_source)
        try:
            response = requests.get(layer_source)
            return HttpResponse(response)
        except (HTTPError, KeyError, ConnectionError) as e:
            print(e)
            return HttpResponse('')
