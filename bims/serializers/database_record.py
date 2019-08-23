from rest_framework import serializers
from bims.models.source_reference import DatabaseRecord


class DatabaseRecordSerializer(serializers.ModelSerializer):
    """
    Serializer for database record of source reference.
    """
    name = serializers.SerializerMethodField()

    class Meta:
        model = DatabaseRecord
        fields = '__all__'

    def get_name(self, obj):
        return obj.__unicode__()
