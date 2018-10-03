from rest_framework import serializers
from rest_framework_gis.serializers import (
    GeoFeatureModelSerializer, GeometrySerializerMethodField)
from bims.models.biological_collection_record import BiologicalCollectionRecord
from bims.serializers.taxon_serializer import (
    TaxonSerializer,
    TaxonExportSerializer
)


class BioCollectionSerializer(serializers.ModelSerializer):
    """
    Serializer for biological collection record.
    """
    location = serializers.SerializerMethodField()
    owner = serializers.SerializerMethodField()
    taxonomy = serializers.SerializerMethodField()

    def get_taxonomy(self, obj):
        return TaxonSerializer(obj.taxon_gbif_id).data

    def get_owner(self, obj):
        return obj.owner.username

    def get_location(self, obj):
        return obj.site.get_geometry().geojson

    class Meta:
        model = BiologicalCollectionRecord
        fields = '__all__'


class BioCollectionDetailSerializer(serializers.ModelSerializer):
    """
    Serializer for biological collection record detail.
    """
    owner = serializers.SerializerMethodField()
    children_fields = serializers.SerializerMethodField()
    validated = serializers.BooleanField(required=True)
    taxonomy = serializers.SerializerMethodField()
    record_type = serializers.SerializerMethodField()

    def get_record_type(self, obj):
        return 'bio'

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
    location_site = serializers.SerializerMethodField()
    latitude = serializers.SerializerMethodField()
    longitude = serializers.SerializerMethodField()
    species_name = serializers.SerializerMethodField()
    notes = serializers.SerializerMethodField()
    category = serializers.SerializerMethodField()
    date = serializers.SerializerMethodField()
    collector = serializers.SerializerMethodField()
    taxon_class = serializers.SerializerMethodField()

    def get_taxon_class(self, obj):
        if obj.taxon_class:
            return obj.taxon_class
        else:
            return ''

    def get_location_site(self, obj):
        if obj.location_site_name:
            return obj.location_site_name.encode('utf8')
        return ''

    def get_latitude(self, obj):
        if obj.location_center:
            return obj.location_center.x
        return ''

    def get_longitude(self, obj):
        if obj.location_center:
            return obj.location_center.y
        return ''

    def get_species_name(self, obj):
        return obj.original_species_name.encode('utf8')

    def get_notes(self, obj):
        return obj.notes.replace(';', '-').encode('utf8')

    def get_category(self, obj):
        return obj.category.encode('utf8')

    def get_date(self, obj):
        if obj.collection_date:
            return obj.collection_date.strftime('%Y-%m-%d')

    def get_collector(self, obj):
        return obj.collector.encode('utf8')

    class Meta:
        model = BiologicalCollectionRecord
        fields = [
            'location_site', 'latitude', 'longitude',
            'species_name', 'notes', 'category',
            'date', 'collector', 'taxon_class']

    def to_representation(self, instance):
        result = super(
            BioCollectionOneRowSerializer, self).to_representation(
            instance)
        return result


class BioCollectionGeojsonSerializer(GeoFeatureModelSerializer):
    geometry = GeometrySerializerMethodField()
    location_site = serializers.SerializerMethodField()
    species_name = serializers.SerializerMethodField()
    notes = serializers.SerializerMethodField()
    category = serializers.SerializerMethodField()
    date = serializers.SerializerMethodField()
    collector = serializers.SerializerMethodField()

    def get_location_site(self, obj):
        if obj.site:
            return obj.site.name
        return ''

    def get_species_name(self, obj):
        return obj.original_species_name

    def get_notes(self, obj):
        return obj.notes

    def get_category(self, obj):
        return obj.category

    def get_date(self, obj):
        if obj.collection_date:
            return obj.collection_date.strftime('%Y-%m-%d')

    def get_collector(self, obj):
        return obj.collector

    def get_geometry(self, obj):
        if obj.site:
            return obj.site.get_geometry()
        return None

    class Meta:
        model = BiologicalCollectionRecord
        geo_field = 'geometry'
        fields = [
            'location_site', 'species_name', 'notes', 'category',
            'date', 'collector']

    def to_representation(self, instance):
        result = super(
            BioCollectionGeojsonSerializer, self).to_representation(
            instance)
        try:
            taxonomy = TaxonExportSerializer(instance.taxon_gbif_id).data
            result['properties'].update(taxonomy)
        except KeyError:
            pass
        return result
