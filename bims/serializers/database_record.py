from rest_framework import serializers
from bims.models.source_reference import DatabaseRecord


class DatabaseRecordSerializer(serializers.ModelSerializer):
    """
    Serializer for database record of source reference.
    """

    class Meta:
        model = DatabaseRecord
        fields = '__all__'
