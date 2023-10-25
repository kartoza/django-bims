import re
import requests
from requests.exceptions import HTTPError, ConnectionError
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.authentication import BasicAuthentication
from bims.permissions.auth_class import CsrfExemptSessionAuthentication
from bims.models.non_biodiversity_layer import (
    NonBiodiversityLayer
)


class GetFeatureInfo(APIView):
    """Request GetFeatureInfo from geoserver"""
    authentication_classes = (CsrfExemptSessionAuthentication,
                              BasicAuthentication)

    def remove_proxy(self, url):
        return re.sub(r'(/?)bims_proxy(/?)|', '', url)

    def post(self, request):
        layer_source = request.POST.get('layerSource', None)
        layer_name = request.POST.get('layerName', None)
        layer = None
        if layer_name:
            try:
                layer = NonBiodiversityLayer.objects.get(
                    wms_layer_name=layer_name
                )
            except NonBiodiversityLayer.DoesNotExist:
                pass
        layer_source = self.remove_proxy(layer_source)
        try:
            response = requests.get(layer_source)
            return Response({
                'feature_data': response.text,
                'layer_attr': layer.layer_csv_attribute if layer else None,
                'layer_id': layer.id if layer else None,
                'document': layer.document.url if layer and layer.document else None,
                'document_title': layer.document_title if layer else None
            })
        except (HTTPError, KeyError, ConnectionError) as e:
            print(e)
            return Response({
                'feature_data': '',
                'layer_attr': None,
                'layer_id': None,
                'document': None,
                'document_title': None
            })
