from braces.views import SuperuserRequiredMixin
from django.views.generic import TemplateView
from rest_framework import serializers, status
from rest_framework.response import Response
from rest_framework.views import APIView

from bims.models.location_context_group import (
    LocationContextGroup
)
from bims.utils.uuid import is_uuid
from cloud_native_gis.models import Layer
from cloud_native_gis.serializer.layer import LayerSerializer


class NativeLayerSerializer(LayerSerializer):
    class Meta:
        model = Layer
        fields = '__all__'


class LocationContextGroupSerializer(serializers.ModelSerializer):

    is_native_layer = serializers.SerializerMethodField()
    native_layer_name = serializers.SerializerMethodField()

    def get_native_layer_name(self, obj: LocationContextGroup):
        if obj.key and is_uuid(obj.key):
            layer = Layer.objects.get(unique_id=obj.key)
            return layer.name
        return ''

    def get_is_native_layer(self, obj: LocationContextGroup):
        if obj.key:
            return is_uuid(obj.key)
        return False

    class Meta:
        model = LocationContextGroup
        fields = '__all__'


class ContextLayersView(SuperuserRequiredMixin, TemplateView):
    template_name = 'context_layers.html'


class ContextLayerGroup(SuperuserRequiredMixin, APIView):

    def post(self, request):
        serializer = LocationContextGroupSerializer(
            data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(
                serializer.data,
                status=status.HTTP_201_CREATED)
        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, pk):
        try:
            group = LocationContextGroup.objects.get(pk=pk)
        except LocationContextGroup.DoesNotExist:
            return Response(
                {'error': 'Group not found'},
                status=status.HTTP_404_NOT_FOUND)

        serializer = LocationContextGroupSerializer(
            group, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST)

    def get(self, request, *args):
        location_context_groups = (
            LocationContextGroup.objects.all().order_by('order')
        )
        context_group_data = LocationContextGroupSerializer(
            location_context_groups, many=True
        )
        return Response(context_group_data.data)


class CloudNativeLayerAutoCompleteAPI(APIView):
    def get(self, request, *args):
        query = request.query_params.get('q', '')
        layers = Layer.objects.filter(
            name__icontains=query
        )
        serializer = NativeLayerSerializer(
            layers, many=True, context={
            'request': request
        })
        return Response(serializer.data)
