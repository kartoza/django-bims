# SPDX-FileCopyrightText: Kartoza
# SPDX-License-Identifier: AGPL-3.0
"""
Serializers for TaxonGroup model in API v1.
"""
from rest_framework import serializers

from bims.models.taxon_group import TaxonGroup


class TaxonGroupSerializer(serializers.ModelSerializer):
    """
    Serializer for TaxonGroup model.

    Represents organism groups like Fish, Invertebrates, etc.
    """

    parent_name = serializers.CharField(source="parent.name", read_only=True)
    taxa_count = serializers.SerializerMethodField()
    logo_url = serializers.SerializerMethodField()

    class Meta:
        model = TaxonGroup
        fields = [
            "id",
            "name",
            "singular_name",
            "category",
            "display_order",
            "parent_name",
            "taxa_count",
            "logo_url",
        ]
        read_only_fields = fields

    def get_taxa_count(self, obj):
        """Return count of taxa in this group."""
        if hasattr(obj, "taxa_count"):
            return obj.taxa_count
        return obj.taxonomies.count()

    def get_logo_url(self, obj):
        """Return logo URL if available."""
        if obj.logo:
            return obj.logo.url
        return None


class TaxonGroupDetailSerializer(TaxonGroupSerializer):
    """
    Detailed serializer for single taxon group.

    Includes additional configuration fields.
    """

    gbif_parent_species_name = serializers.CharField(
        source="gbif_parent_species.canonical_name", read_only=True
    )
    taxa_upload_template_url = serializers.SerializerMethodField()
    occurrence_upload_template_url = serializers.SerializerMethodField()

    class Meta:
        model = TaxonGroup
        fields = TaxonGroupSerializer.Meta.fields + [
            "source_collection",
            "gbif_parent_species_name",
            "chart_data",
            "level",
            "taxa_upload_template_url",
            "occurrence_upload_template_url",
        ]
        read_only_fields = fields

    def get_taxa_upload_template_url(self, obj):
        """Return taxa upload template URL if available."""
        if obj.taxa_upload_template:
            return obj.taxa_upload_template.url
        return None

    def get_occurrence_upload_template_url(self, obj):
        """Return occurrence upload template URL if available."""
        if obj.occurrence_upload_template:
            return obj.occurrence_upload_template.url
        return None
