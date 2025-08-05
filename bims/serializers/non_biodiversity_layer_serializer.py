from rest_framework import serializers
from bims.models import NonBiodiversityLayer, LayerGroup


class NonBiodiversityLayerSerializer(serializers.ModelSerializer):
    """
    Serializer for NonBiodiversityLayer model.
    """
    native_layer_url = serializers.SerializerMethodField()
    native_layer_style = serializers.SerializerMethodField()
    native_layer_abstract = serializers.SerializerMethodField()
    native_style_id = serializers.SerializerMethodField()
    pmtiles = serializers.SerializerMethodField()
    attribution = serializers.SerializerMethodField()
    type = serializers.SerializerMethodField()

    def get_type(self, obj):
        return 'Layer'

    def get_native_style_id(self, obj: NonBiodiversityLayer):
        if obj.native_layer_style:
            return obj.native_layer_style.id
        return None

    def get_native_layer_abstract(self, obj: NonBiodiversityLayer):
        if not obj.native_layer:
            return ''
        if not obj.native_layer.abstract:
            return ''
        return obj.native_layer.abstract

    def get_pmtiles(self, obj: NonBiodiversityLayer):
        request = self.context.get('request', None)
        if not obj.native_layer:
            return ''
        if not obj.native_layer.pmtile:
            return ''
        return (
            obj.native_layer.absolute_pmtiles_url(request)
        ).replace('pmtiles://', '')

    def get_native_layer_url(self, obj: NonBiodiversityLayer) -> str:
        if obj.native_layer:
            return obj.native_layer.tile_url
        return ''

    def get_attribution(self, obj: NonBiodiversityLayer) -> str:
        if obj.native_layer and obj.native_layer.attribution:
            return obj.native_layer.attribution
        return ''

    def get_native_layer_style(self, obj: NonBiodiversityLayer) -> str:
        if obj.native_layer_style:
            return obj.native_layer_style.style
        return ''

    class Meta:
        model = NonBiodiversityLayer
        fields = '__all__'


class NonBiodiversityLayerGroupSerializer(serializers.ModelSerializer):
    layers = serializers.SerializerMethodField()
    type = serializers.SerializerMethodField()

    def get_type(self, obj):
        return 'LayerGroup'

    class Meta:
        model = LayerGroup
        fields = (
            "id", "type", "name", "slug", "description", "order", "layers"
        )

    def get_layers(self, obj):
        # delegate to the existing layer serializer
        return NonBiodiversityLayerSerializer(
            obj.layers.all().order_by("order"),
            many=True,
            context=self.context,
        ).data
