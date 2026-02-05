from rest_framework import serializers
from taggit.models import Tag

from bims.models.taxonomy import Taxonomy, TaxonTag
from bims.models.taxon_tag_description import TaxonTagDescription


class TagSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()
    description = serializers.SerializerMethodField()

    def get_name(self, obj):
        if isinstance(obj, TaxonTag):
            return f'{obj.name} {"(?)" if obj.doubtful else ""}'
        return obj.name

    def get_description(self, obj):
        try:
            return obj.description_detail.description
        except TaxonTagDescription.DoesNotExist:
            return ''
        except AttributeError:
            return ''

    class Meta:
        model = Tag
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
