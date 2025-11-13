from rest_framework import serializers
from taggit.models import Tag

from bims.models.taxonomy import Taxonomy, TaxonTag


class TagSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()

    def get_name(self, obj):
        if isinstance(obj, TaxonTag):
            return f'{obj.name} {"(?)" if obj.doubtful else ""}'.strip()
        return obj.name.strip()

    class Meta:
        model = TaxonTag
        fields = ['id', 'name', 'description']


class TaxonomyTagUpdateSerializer(serializers.ModelSerializer):
    tags = serializers.ListField(
        child=serializers.CharField(max_length=100),
        write_only=True
    )

    class Meta:
        model = Taxonomy
        fields = ['id', 'tags']

    def update(self, instance, validated_data):
        tags_data = validated_data.pop('tags')
        instance.tags.clear()
        for tag_name in tags_data:
            tag, created = Tag.objects.get_or_create(name=tag_name)
            instance.tags.add(tag)
        return instance
