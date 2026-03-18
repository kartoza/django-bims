# SPDX-FileCopyrightText: Kartoza
# SPDX-License-Identifier: AGPL-3.0
"""
Serializers for SourceReference model in API v1.
"""
from rest_framework import serializers

from bims.models.source_reference import SourceReference


class SourceReferenceSerializer(serializers.ModelSerializer):
    """
    Serializer for SourceReference model.

    Handles polymorphic source references (Bibliography, Document, Database).
    """

    title = serializers.SerializerMethodField()
    authors = serializers.SerializerMethodField()
    year = serializers.SerializerMethodField()
    url = serializers.SerializerMethodField()
    reference_type = serializers.CharField(read_only=True)

    class Meta:
        model = SourceReference
        fields = [
            "id",
            "title",
            "authors",
            "year",
            "reference_type",
            "url",
            "note",
            "source_name",
        ]
        read_only_fields = fields

    def get_title(self, obj):
        """Return title from the source."""
        try:
            return obj.title
        except AttributeError:
            return obj.source_name or None

    def get_authors(self, obj):
        """Return authors from the source."""
        try:
            return obj.authors
        except AttributeError:
            return None

    def get_year(self, obj):
        """Return publication year from the source."""
        try:
            return obj.year
        except AttributeError:
            return None

    def get_url(self, obj):
        """Return URL or DOI from the source."""
        try:
            if hasattr(obj, "source") and obj.source:
                return obj.source.doi or obj.source.url
        except AttributeError:
            pass

        if obj.is_published_report():
            try:
                if obj.source.doc_file:
                    return obj.source.doc_file.url
                return obj.source.doc_url
            except AttributeError:
                pass

        return None


class SourceReferenceDetailSerializer(SourceReferenceSerializer):
    """
    Detailed serializer for single source reference.
    """

    record_count = serializers.SerializerMethodField()

    class Meta:
        model = SourceReference
        fields = SourceReferenceSerializer.Meta.fields + [
            "record_count",
        ]
        read_only_fields = fields

    def get_record_count(self, obj):
        """Return count of biological records using this reference."""
        if hasattr(obj, "record_count"):
            return obj.record_count
        return obj.biologicalcollectionrecord_set.count()
