# coding=utf8
import csv
import re

from django.contrib.sites.models import Site
from django.db.models import Q
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
                NonBiodiversityLayer.objects.filter(
                    Q(source_site=Site.objects.get_current()) |
                    Q(additional_sites__in=[Site.objects.get_current().id])
                ).order_by('order'),
                many=True).data
        )


class DownloadLayerData(APIView):
    """
    Download layer data from non biodiversity layer
    """
    permission_classes = [IsAuthenticated,]
    _layer = None

    @staticmethod
    def contains_decimal(s):
        pattern = r'-?\d+\.\d+'
        return bool(re.search(pattern, s))

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
                cleaned_row = {key.replace("\ufeff", ""): value for key, value in row.items()}
                if self._layer.csv_attribute not in cleaned_row:
                    return self._get_response(
                        message='CSV attribute not found'
                    )
                if not self.contains_decimal(
                    cleaned_row[self._layer.csv_attribute]
                ) and self.contains_decimal(
                    query_filter
                ):
                    query_filter = query_filter.split('.')[0]
                if cleaned_row[self._layer.csv_attribute] == query_filter:
                    data = cleaned_row
        return self._get_response(
            message,
            data
        )
