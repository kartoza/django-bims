# coding=utf8
import csv
import re

from braces.views import SuperuserRequiredMixin
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from bims.models.non_biodiversity_layer import NonBiodiversityLayer, LayerGroup
from bims.serializers.non_biodiversity_layer_serializer import (
    NonBiodiversityLayerSerializer, NonBiodiversityLayerGroupSerializer
)
from cloud_native_gis.models import Style


class NonBiodiversityLayerList(APIView):
    """
    Returns all non-biodiversity-layers, grouped by NonBiodiversityLayerGroup.
    """

    def get(self, request, format=None):
        groups = LayerGroup.objects.prefetch_related(
            "layers__native_layer",
            "layers__native_layer_style",
            "layers__layer_groups",
        ).order_by("order")

        ungrouped_layers = (
            NonBiodiversityLayer.objects.filter(layer_groups=None)
            .order_by("order")
            .select_related("native_layer", "native_layer_style")
        )

        serialized = [
            *NonBiodiversityLayerGroupSerializer(
                groups, many=True, context={"request": request}).data,
            *NonBiodiversityLayerSerializer(
                ungrouped_layers, many=True, context={"request": request}).data,
        ]

        return Response(
            [
                {**layer, 'order': index + 1}
                for index, layer in enumerate(
                    sorted(serialized, key=lambda d: d['order'])
                )
            ]
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


class VisualizationLayers(SuperuserRequiredMixin, APIView):
    def get(self, request, *args):
        visualization_layers = (
            NonBiodiversityLayer.objects.all().order_by(
                'order')
        )
        visualization_layers_data = NonBiodiversityLayerSerializer(
            visualization_layers, many=True, context={
                'request': request
            }
        )
        return Response(visualization_layers_data.data)

    def post(self, request, *args):
        data = request.data
        layer_type = data.get('layer_type', 'wms')
        name = data.get('name')
        layer_id = data.get('layer_id')
        layer_style = data.get('style_id')
        wms_layer_url = data.get('wms_layer_url')
        wms_layer_name = data.get('wms_layer_name')
        abstract = data.get('abstract', '')
        order = NonBiodiversityLayer.objects.all().count() + 1

        if layer_type == 'native_layer':
            non_biodiversity_layer = NonBiodiversityLayer.objects.create(
                name=name,
                wms_layer_name=name,
                native_layer_id=int(layer_id),
                native_layer_style_id=int(layer_style),
                order=order
            )
            non_biodiversity_layer.native_layer.abstract = abstract
            non_biodiversity_layer.native_layer.save()
            return Response(
                {
                    "message": "layer created successfully.",
                }, status=201)
        elif layer_type == 'wms':
            NonBiodiversityLayer.objects.create(
                name=name,
                wms_url=wms_layer_url,
                wms_layer_name=wms_layer_name,
                order=order
            )
            return Response(
                {
                    "message": "layer created successfully.",
                }, status=201)
        return Response('Error', status=400)

    def delete(self, request, *args):
        layer_id = request.query_params.get('id')

        if not layer_id:
            return Response({"error": "id is required."}, status=400)

        layer = NonBiodiversityLayer.objects.filter(
            id=layer_id
        )
        if layer.exists():
            layer.delete()
            return Response({
                "message": f"Layer {id} deleted successfully."},
                status=204)
        else:
            return Response({
                "error": f"Layer with id {id} not found."}, status=404)

    def put(self, request, *args):
        """Update the order of visualization layers."""
        data = request.data
        layers_data = data.get('layers', [])

        # Update filter order
        for layer_data in layers_data:
            layer_id = layer_data.get('id')
            new_order = layer_data.get('display_order')
            NonBiodiversityLayer.objects.filter(
                id=layer_id).update(order=new_order)

        if data.get('id'):
            try:
                layer_instance = NonBiodiversityLayer.objects.get(
                    id=data.get('id'))
                serializer = NonBiodiversityLayerSerializer(
                    instance=layer_instance,
                    data=request.data,
                    partial=True,
                    context={
                        'request': request
                    }
                )
                if serializer.is_valid():
                    validated_data = serializer.validated_data
                    layer_instance.name = validated_data.get(
                        'name', layer_instance.name)
                    layer_instance.order = validated_data.get(
                        'order', layer_instance.order)
                    layer_instance.wms_layer_name = validated_data.get(
                        'wms_layer_name', layer_instance.wms_layer_name)
                    layer_instance.wms_url = validated_data.get(
                        'wms_url', layer_instance.wms_url)
                    layer_instance.native_layer_id = data.get(
                        'native_layer',
                        layer_instance.native_layer.id if layer_instance.native_layer else None
                    )
                    layer_instance.native_layer_style_id = data.get(
                        'native_layer_style',
                        layer_instance.native_layer_style.id if layer_instance.native_layer_style else None
                    )
                    layer_instance.save()

                    if layer_instance.native_layer:
                        layer_instance.native_layer.abstract = data.get(
                            'abstract', ''
                        )
                        layer_instance.native_layer.save()

                    return Response(
                        NonBiodiversityLayerSerializer(
                            layer_instance,
                            context={
                                'request': request
                            }
                        ).data,
                        status=200)
                else:
                    return Response(serializer.errors, status=400)
            except NonBiodiversityLayer.DoesNotExist:
                return Response({'error': 'Layer not found.'}, status=404)

        return Response(
            {"message": "Order updated successfully."}, status=200)
