from rest_framework import serializers
from bims.models.biological_collection_record import BiologicalCollectionRecord


class BioCollectionSerializer(serializers.ModelSerializer):
    """
    Serializer for biological collection record.
    """
    owner = serializers.SerializerMethodField()
    children_fields = serializers.SerializerMethodField()

    def get_owner(self, obj):
        if obj.owner:
            return '%s,%s' % (obj.owner.pk, obj.owner.username)

    def get_children_fields(self, obj):
        children_records = {}
        children = obj.get_children()
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
