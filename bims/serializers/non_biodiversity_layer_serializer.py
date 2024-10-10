from rest_framework import serializers
from bims.models import NonBiodiversityLayer


class NonBiodiversityLayerSerializer(serializers.ModelSerializer):
    """
    Serializer for NonBiodiversityLayer model.
    """
    native_layer_url = serializers.SerializerMethodField()
    native_layer_style = serializers.SerializerMethodField()
    pmtiles = serializers.SerializerMethodField()
    attribution = serializers.SerializerMethodField()

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
