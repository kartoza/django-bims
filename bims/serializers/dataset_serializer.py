from rest_framework import serializers
from bims.models.dataset import Dataset


class DatasetSerializer(serializers.ModelSerializer):
    class Meta:
        model = Dataset
        fields = ['id', 'name', 'abbreviation']
