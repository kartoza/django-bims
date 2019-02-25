from rest_framework import serializers
from bims.models import Taxon, Taxonomy
from bims.models.iucn_status import IUCNStatus
from bims.serializers.document_serializer import DocumentSerializer


class TaxonSerializer(serializers.ModelSerializer):
    """
    Serializer for taxon collection model.
    """
    iucn_status_sensitive = serializers.SerializerMethodField()
    iucn_status_name = serializers.SerializerMethodField()
    iucn_status_full_name = serializers.SerializerMethodField()
    iucn_status_colour = serializers.SerializerMethodField()
    record_type = serializers.SerializerMethodField()
    documents = DocumentSerializer(many=True)

    def get_record_type(self, obj):
        return 'bio'

    def get_iucn_status_sensitive(self, obj):
        if obj.iucn_status:
            return obj.iucn_status.sensitive
        else:
            return None

    def get_iucn_status_name(self, obj):
        if obj.iucn_status:
            return obj.iucn_status.category
        else:
            return None

    def get_iucn_status_full_name(self, obj):
        if obj.iucn_status:
            for value in IUCNStatus.CATEGORY_CHOICES:
                if value[0] == obj.iucn_status.category:
                    return value[1]
            return None
        else:
            return None

    def get_iucn_status_colour(self, obj):
        if obj.iucn_status:
            return obj.iucn_status.colour
        else:
            return None

    class Meta:
        model = Taxonomy
        fields = '__all__'


class TaxonExportSerializer(serializers.ModelSerializer):
    """
    Serializer for taxon collection model.
    """
    iucn_status_sensitive = serializers.SerializerMethodField()
    iucn_status_name = serializers.SerializerMethodField()

    def get_iucn_status_sensitive(self, obj):
        if obj.iucn_status:
            return obj.iucn_status.sensitive
        else:
            return None

    def get_iucn_status_name(self, obj):
        if obj.iucn_status:
            return obj.iucn_status.category
        else:
            return None

    class Meta:
        model = Taxonomy
        fields = [
            'scientific_name', 'class_name',
            'iucn_status_sensitive', 'iucn_status_name'
        ]


class TaxonOccurencesSerializer(serializers.ModelSerializer):
    """
    Serializer for taxon collection model in occurrences format.
    """

    record_type = serializers.SerializerMethodField()
    count = serializers.SerializerMethodField()

    def get_record_type(self, obj):
        return 'taxa'

    def get_count(self, obj):
        if hasattr(obj, 'num_occurrences'):
            return obj.num_occurrences
        else:
            return 0

    class Meta:
        model = Taxon
        fields = [
            'id', 'common_name', 'highlighted_common_name',
            'taxon_class', 'record_type',
            'count'
        ]


class TaxonSimpleSerialializer(serializers.ModelSerializer):
    class Meta:
        model = Taxon
        fields = ['id', 'common_name', 'scientific_name']
