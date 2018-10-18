import requests
from requests.exceptions import HTTPError
from django.http import HttpResponse
from rest_framework.views import APIView
from rest_framework.authentication import BasicAuthentication
from bims.permissions.auth_class import CsrfExemptSessionAuthentication


class GetFeatureInfo(APIView):
    """Request GetFeatureInfo from geoserver"""
    authentication_classes = (CsrfExemptSessionAuthentication,
                              BasicAuthentication)

    def post(self, request):
        layer_source = request.POST.get('layerSource', None)

        try:
            response = requests.get(layer_source)
            return HttpResponse(response)
        except (HTTPError, KeyError) as e:
            print(e)
            return HttpResponse('')
