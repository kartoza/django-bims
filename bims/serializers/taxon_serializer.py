from rest_framework import serializers
from bims.models import Taxon


class TaxonSerializer(serializers.ModelSerializer):
    """
    Serializer for taxon collection model.
    """
    iucn_status_sensitive = serializers.SerializerMethodField()
    iucn_status_name = serializers.SerializerMethodField()
    record_type = serializers.SerializerMethodField()
    count = serializers.SerializerMethodField()
    taxon_gbif_id = serializers.SerializerMethodField()

    def get_taxon_gbif_id(self, obj):
        return obj.id

    def get_record_type(self, obj):
        if 'record_type' in self.context:
            return self.context['record_type']
        return 'taxa'

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

    def get_count(self, obj):
        if hasattr(obj, 'num_occurences'):
            return obj.num_occurences
        else:
            return 0

    class Meta:
        model = Taxon
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
        model = Taxon
        fields = [
            'scientific_name', 'kingdom', 'phylum',
            'taxon_class', 'order', 'family', 'genus', 'species',
            'iucn_status_sensitive', 'iucn_status_name'
        ]
