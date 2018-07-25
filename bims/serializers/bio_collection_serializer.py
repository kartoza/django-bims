from rest_framework import serializers
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

    def get_owner(self, obj):
        if obj.owner:
            return '%s,%s' % (obj.owner.pk, obj.owner.username)

    class Meta:
        model = BiologicalCollectionRecord
        fields = '__all__'

    def to_representation(self, instance):
        result = super(BioCollectionOneRowSerializer, self).to_representation(instance)
        taxonomy = TaxonSerializer(instance.taxon_gbif_id).data
        result.update(taxonomy)
        return result
