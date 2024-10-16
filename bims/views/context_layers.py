from braces.views import SuperuserRequiredMixin
from django.views.generic import TemplateView
from django_tenants.utils import get_tenant
from rest_framework import serializers, status
from rest_framework.response import Response
from rest_framework.views import APIView

from bims.models.location_context_group import (
    LocationContextGroup
)
from bims.models.location_context_filter import (
    LocationContextFilter
)
from bims.models.location_context_filter_group_order import (
    LocationContextFilterGroupOrder
)
from bims.utils.uuid import is_uuid
from bims.tasks.location_context import generate_spatial_scale_filter
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


class LocationFilterGroupSerializer(serializers.ModelSerializer):
    group = LocationContextGroupSerializer(many=False)

    class Meta:
        model = LocationContextFilterGroupOrder
        fields = '__all__'


class LocationFilterSerializer(serializers.ModelSerializer):
    location_context_groups = serializers.SerializerMethodField()

    def get_location_context_groups(self, obj):
        filter_group_orders = (
            LocationContextFilterGroupOrder.objects.filter(filter=obj)
        )
        return (
            LocationFilterGroupSerializer(
                filter_group_orders,
                many=True).data
        )

    class Meta:
        model = LocationContextFilter
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


class ContextFilter(SuperuserRequiredMixin, APIView):
    def get(self, request, *args):
        context_filters = (
            LocationContextFilter.objects.all().order_by(
                'display_order')
        )
        context_filter_data = LocationFilterSerializer(
            context_filters, many=True
        )
        return Response(context_filter_data.data)

    def put(self, request, *args):
        """Update the order of context filters and groups."""
        data = request.data
        filters_data = data.get('filters', [])
        groups_data = data.get('groups', {})

        # Update filter order
        for filter_data in filters_data:
            filter_id = filter_data.get('id')
            new_order = filter_data.get('display_order')
            LocationContextFilter.objects.filter(id=filter_id).update(display_order=new_order)

        # Update group order within each filter
        for filter_id, groups in groups_data.items():
            for group_data in groups:
                group_id = group_data.get('id')
                new_group_order = group_data.get('group_display_order')
                context_filter_group = LocationContextFilterGroupOrder.objects.filter(
                    filter_id=filter_id,
                    group_id=group_id
                )
                if context_filter_group.exists():
                    context_filter_group.update(group_display_order=new_group_order)
                else:
                    LocationContextFilterGroupOrder.objects.create(
                        filter_id=filter_id,
                        group_id=group_id,
                        group_display_order=new_group_order
                    )

        tenant_id = get_tenant(request).id
        generate_spatial_scale_filter.delay(tenant_id)

        return Response({"message": "Order updated successfully."}, status=200)


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
