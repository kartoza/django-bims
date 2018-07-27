from rest_framework import serializers
from rest_framework_gis.serializers import (
    GeoFeatureModelSerializer, GeometrySerializerMethodField)
from bims.models.biological_collection_record import BiologicalCollectionRecord
from bims.serializers.taxon_serializer import TaxonSerializer


class BioCollectionSerializer(serializers.ModelSerializer):
    """
    Serializer for biological collection record.
    """
    owner = serializers.SerializerMethodField()
    children_fields = serializers.SerializerMethodField()
    validated = serializers.BooleanField(required=True)
    taxonomy = serializers.SerializerMethodField()

    def get_taxonomy(self, obj):
        return TaxonSerializer(obj.taxon_gbif_id).data

    def get_owner(self, obj):
        if obj.owner:
            return '%s,%s' % (obj.owner.pk, obj.owner.username)

    def get_children_fields(self, obj):
        children_records = {}
        children = obj.get_children()
        if not children:
            return {'name': 'base'}

        children_records['name'] = children._meta.verbose_name
        fields = children._meta.get_fields(include_parents=False)
        for field in fields:
            if field.primary_key:
                continue
            children_records[field.name] = getattr(children, field.name)
        return children_records

    class Meta:
        model = BiologicalCollectionRecord
        fields = '__all__'


class BioCollectionOneRowSerializer(serializers.ModelSerializer):
    """
    Serializer for biological collection record.
    """
    owner = serializers.SerializerMethodField()
    validated = serializers.BooleanField(required=True)
    x = serializers.SerializerMethodField()
    y = serializers.SerializerMethodField()
    site = serializers.SerializerMethodField()

    def get_x(self, obj):
        if obj.site and obj.site.geometry_point:
            return obj.site.geometry_point.x
        return ''

    def get_y(self, obj):
        if obj.site and obj.site.geometry_point:
            return obj.site.geometry_point.y
        return ''

    def get_site(self, obj):
        if obj.site:
            return obj.site.name
        return ''

    def get_owner(self, obj):
        if obj.owner:
            return '%s,%s' % (obj.owner.pk, obj.owner.username)

    class Meta:
        model = BiologicalCollectionRecord
        fields = '__all__'

    def to_representation(self, instance):
        result = super(BioCollectionOneRowSerializer, self).to_representation(
            instance)
        taxonomy = TaxonSerializer(instance.taxon_gbif_id).data
        result.update(taxonomy)
        return result


class BioCollectionGeojsonSerializer(GeoFeatureModelSerializer):
    geometry = GeometrySerializerMethodField()
    site = serializers.SerializerMethodField()

    def get_geometry(self, obj):
        if obj.site:
            return obj.site.get_geometry()
        return None

    def get_site(self, obj):
        if obj.site:
            return obj.site.name
        return ''

    class Meta:
        model = BiologicalCollectionRecord
        geo_field = 'geometry'
        exclude = []

    def to_representation(self, instance):
        result = super(BioCollectionGeojsonSerializer, self).to_representation(
            instance)
        try:
            taxonomy = TaxonSerializer(instance.taxon_gbif_id).data
            result['properties'].update(taxonomy)
        except KeyError:
            pass
        return result
