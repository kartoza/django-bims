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
    owner_email = serializers.SerializerMethodField()
    taxonomy = serializers.SerializerMethodField()
    site_name = serializers.SerializerMethodField()

    def get_site_name(self, obj):
        return obj.site.name

    def get_taxonomy(self, obj):
        return TaxonSerializer(obj.taxonomy).data

    def get_owner(self, obj):
        return obj.owner.username

    def get_owner_email(self, obj):
        return obj.owner.email

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
        return TaxonSerializer(obj.taxonomy).data

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
    origin = serializers.SerializerMethodField()
    date = serializers.SerializerMethodField()
    collector = serializers.SerializerMethodField()
    taxon_class = serializers.SerializerMethodField()
    reference = serializers.SerializerMethodField()
    reference_category = serializers.SerializerMethodField()

    def get_taxon_class(self, obj):
        return obj.taxonomy.class_name

    def get_location_site(self, obj):
        return obj.site.name.encode('utf8')

    def get_latitude(self, obj):
        lat = obj.site.get_centroid().x
        return lat

    def get_longitude(self, obj):
        lon = obj.site.get_centroid().y
        return lon

    def get_origin(self, obj):
        category = obj.category
        for choice in BiologicalCollectionRecord.CATEGORY_CHOICES:
            if choice[0] == obj.category:
                category = choice[1]

        return category.encode('utf8')

    def get_date(self, obj):
        if obj.collection_date:
            return obj.collection_date.strftime('%Y-%m-%d')

    def get_reference(self, obj):
        return obj.reference.encode('utf8')

    def get_reference_category(self, obj):
        return obj.reference_category.encode('utf8')

    def get_collector(self, obj):
        return obj.collector.encode('utf8')

    class Meta:
        model = BiologicalCollectionRecord
        fields = [
            'location_site', 'latitude', 'longitude',
            'original_species_name', 'notes', 'origin',
            'date', 'collector', 'taxon_class',
            'reference', 'reference_category']

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
            taxonomy = TaxonExportSerializer(instance.taxonomy).data
            result['properties'].update(taxonomy)
        except KeyError:
            pass
        return result
