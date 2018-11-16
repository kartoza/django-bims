from rest_framework import serializers
from geonode.documents.models import Document


class DocumentSerializer(serializers.ModelSerializer):
    """
    Serializer for documents.
    """
    class Meta:
        model = Document
        fields = [
            'id',
            'uuid',
            'title',
            'abstract',
            'owner',
            'group',
            'thumbnail_url',
            'detail_url',
            'doc_file']
