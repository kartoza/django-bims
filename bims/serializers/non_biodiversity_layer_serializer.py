from rest_framework import serializers
from bims.models import NonBiodiversityLayer


class NonBiodiversityLayerSerializer(serializers.ModelSerializer):
    """
    Serializer for NonBiodiversityLayer model.
    """

    class Meta:
        model = NonBiodiversityLayer
        fields = '__all__'
