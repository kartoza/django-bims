# coding=utf8
import csv

from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from bims.models.non_biodiversity_layer import NonBiodiversityLayer
from bims.serializers.non_biodiversity_layer_serializer import (
    NonBiodiversityLayerSerializer
)


class NonBiodiversityLayerList(APIView):
    """
    List of all non_biodiversity_layer information
    """

    def get(self, request, format=None):
        return Response(
            NonBiodiversityLayerSerializer(
                NonBiodiversityLayer.objects.all().order_by('order'),
                many=True).data
        )


class DownloadLayerData(APIView):
    """
    Download layer data from non biodiversity layer
    """
    permission_classes = [IsAuthenticated,]
    _layer = None

    def _get_response(self, message, data=None):
        return Response({
            'layer': self._layer.name if self._layer else None,
            'message': message,
            'data': data
        })

    def get(self, request, layer_id, query_filter):
        try:
            self._layer = NonBiodiversityLayer.objects.get(
                id=layer_id
            )
        except NonBiodiversityLayer.DoesNotExist:
            return self._get_response(
                message='Layer not found'
            )
        message = 'ok'
        data = None

        if not self._layer.csv_file:
            return self._get_response(
                message='CSV file not found for this layer'
            )

        with open(self._layer.csv_file.path) as csv_file:
            csv_reader = csv.DictReader(csv_file)
            for row in csv_reader:
                if self._layer.csv_attribute not in row:
                    return self._get_response(
                        message='CSV attribute not found'
                    )
                if row[self._layer.csv_attribute] == query_filter:
                    data = row
        return self._get_response(
            message,
            data
        )
