from rest_framework import serializers
from django.utils.html import escape


from bims.models.source_reference import SourceReference


class SourceReferenceSerializer(serializers.ModelSerializer):

    title = serializers.SerializerMethodField()
    reference_source = serializers.SerializerMethodField()
    year = serializers.SerializerMethodField()
    authors = serializers.SerializerMethodField()
    reference_type = serializers.SerializerMethodField()
    link_template = serializers.SerializerMethodField()

    def get_link_template(self, obj):
        return obj.link_template()

    def get_reference_type(self, obj):
        return obj.reference_type

    def get_title(self, obj):
        return obj.title

    def get_reference_source(self, obj):
        return obj.reference_source

    def get_year(self, obj):
        return obj.year

    def get_authors(self, obj):
        return obj.authors

    class Meta:
        model = SourceReference
        fields = ['id', 'source_name', 'title', 'reference_source', 'year',
                  'authors', 'reference_type', 'link_template']
