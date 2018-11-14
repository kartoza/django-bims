from rest_framework import serializers
from td_biblio.models import Entry


class ReferenceSerializer(serializers.ModelSerializer):
    """
    Serializer for cluster model.
    """
    class Meta:
        model = Entry
        fields = '__all__'
