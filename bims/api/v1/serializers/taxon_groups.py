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

    parent_id = serializers.IntegerField(source="parent.id", read_only=True, allow_null=True)
    parent_name = serializers.CharField(source="parent.name", read_only=True)
    taxa_count = serializers.SerializerMethodField()
    logo_url = serializers.SerializerMethodField()
    proposed_by_username = serializers.CharField(source="proposed_by.username", read_only=True)
    approved_by_username = serializers.CharField(source="approved_by.username", read_only=True)
    children = serializers.SerializerMethodField()
    validation_stats = serializers.SerializerMethodField()

    class Meta:
        model = TaxonGroup
        fields = [
            "id",
            "name",
            "singular_name",
            "category",
            "display_order",
            "parent_id",
            "parent_name",
            "taxa_count",
            "logo_url",
            "is_approved",
            "proposed_by_username",
            "approved_by_username",
            "approved_at",
            "rejection_reason",
            "children",
            "validation_stats",
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

    def get_children(self, obj):
        """Return child taxon groups."""
        children = TaxonGroup.objects.filter(parent=obj, is_approved=True).order_by("display_order", "name")
        # Prevent infinite recursion by not including children of children here
        return [{"id": c.id, "name": c.name} for c in children]

    def get_validation_stats(self, obj):
        """Return validation statistics for this group."""
        from bims.models.taxonomy import Taxonomy
        from django.db.models import Q, Count

        # Get taxa in this group
        taxa_qs = Taxonomy.objects.filter(taxongroup=obj)

        # Count validated vs unvalidated, and accepted vs synonym
        stats = taxa_qs.aggregate(
            accepted_validated=Count("id", filter=Q(validated=True, taxonomic_status="ACCEPTED")),
            synonym_validated=Count("id", filter=Q(validated=True) & ~Q(taxonomic_status="ACCEPTED")),
            accepted_unvalidated=Count("id", filter=Q(validated=False, taxonomic_status="ACCEPTED")),
            synonym_unvalidated=Count("id", filter=Q(validated=False) & ~Q(taxonomic_status="ACCEPTED")),
        )
        stats["total_unvalidated"] = stats["accepted_unvalidated"] + stats["synonym_unvalidated"]
        return stats


class TaxonGroupCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating/updating TaxonGroup.
    """

    class Meta:
        model = TaxonGroup
        fields = [
            "id",
            "name",
            "singular_name",
            "category",
            "display_order",
            "parent",
            "source_collection",
            "chart_data",
            "level",
        ]
        read_only_fields = ["id"]


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
