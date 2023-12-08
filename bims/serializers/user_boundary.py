from rest_framework import serializers
from bims.models import UserBoundary


class UserBoundarySerializer(serializers.ModelSerializer):
    """
    Serializer for user boundary model.
    """
    class Meta:
        model = UserBoundary
        fields = [
            'id',
            'user',
            'name',
            'upload_date'
        ]
