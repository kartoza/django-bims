# SPDX-FileCopyrightText: Kartoza
# SPDX-License-Identifier: AGPL-3.0
"""
Serializers for Taxonomy model in API v1.
"""
from rest_framework import serializers

from bims.models.taxonomy import Taxonomy
from bims.models.iucn_status import IUCNStatus
from bims.models.endemism import Endemism


class IUCNStatusSerializer(serializers.ModelSerializer):
    """Serializer for IUCN conservation status."""

    class Meta:
        model = IUCNStatus
        fields = ["id", "category", "sensitive"]


class EndemismSerializer(serializers.ModelSerializer):
    """Serializer for endemism status."""

    class Meta:
        model = Endemism
        fields = ["id", "name", "description"]


class TaxonomyListSerializer(serializers.ModelSerializer):
    """
    Serializer for listing taxonomy records.

    Provides essential fields for list views.
    """

    iucn_status = IUCNStatusSerializer(read_only=True)
    national_conservation_status = IUCNStatusSerializer(read_only=True)
    endemism = EndemismSerializer(read_only=True)
    common_name = serializers.SerializerMethodField()
    record_count = serializers.SerializerMethodField()

    class Meta:
        model = Taxonomy
        fields = [
            "id",
            "scientific_name",
            "canonical_name",
            "rank",
            "taxonomic_status",
            "iucn_status",
            "national_conservation_status",
            "endemism",
            "common_name",
            "gbif_key",
            "verified",
            "record_count",
        ]
        read_only_fields = fields

    def get_common_name(self, obj):
        """Return first vernacular name if available."""
        vernacular = obj.vernacular_names.first()
        return vernacular.name if vernacular else None

    def get_record_count(self, obj):
        """Return count of biological records for this taxon."""
        # This can be optimized with annotate in the queryset
        if hasattr(obj, "record_count"):
            return obj.record_count
        return None


class TaxonomyDetailSerializer(TaxonomyListSerializer):
    """
    Detailed serializer for single taxonomy record.

    Includes full hierarchical data, tags, and vernacular names.
    """

    parent = serializers.SerializerMethodField()
    vernacular_names = serializers.SerializerMethodField()
    tags = serializers.SerializerMethodField()
    biographic_distributions = serializers.SerializerMethodField()
    hierarchy = serializers.SerializerMethodField()
    images = serializers.SerializerMethodField()

    class Meta:
        model = Taxonomy
        fields = TaxonomyListSerializer.Meta.fields + [
            "parent",
            "vernacular_names",
            "tags",
            "biographic_distributions",
            "hierarchy",
            "images",
            "author",
            "legacy_canonical_name",
            "origin",
            "additional_data",
            "hierarchical_data",
            "iucn_redlist_id",
            "iucn_data",
            "fada_id",
        ]
        read_only_fields = fields

    def get_parent(self, obj):
        """Return parent taxonomy details."""
        if not obj.parent:
            return None
        return {
            "id": obj.parent.id,
            "scientific_name": obj.parent.scientific_name,
            "canonical_name": obj.parent.canonical_name,
            "rank": obj.parent.rank,
        }

    def get_vernacular_names(self, obj):
        """Return all vernacular names."""
        return [{"id": v.id, "name": v.name, "language": v.language} for v in obj.vernacular_names.all()]

    def get_tags(self, obj):
        """Return all tags."""
        return list(obj.tags.names())

    def get_biographic_distributions(self, obj):
        """Return biographic distribution tags."""
        return [{"name": tag.name, "doubtful": tag.doubtful} for tag in obj.biographic_distributions.all()]

    def get_hierarchy(self, obj):
        """Return taxonomic hierarchy from root to this taxon."""
        hierarchy = []
        current = obj
        visited = set()
        max_depth = 20

        while current and len(hierarchy) < max_depth:
            if current.id in visited:
                break
            visited.add(current.id)
            hierarchy.insert(
                0,
                {
                    "id": current.id,
                    "name": current.canonical_name or current.scientific_name,
                    "rank": current.rank,
                },
            )
            current = current.parent

        return hierarchy

    def get_images(self, obj):
        """Return taxon images if available."""
        # This would need to be connected to the TaxonImage model
        if hasattr(obj, "taxon_images"):
            return [{"id": img.id, "url": img.source if hasattr(img, "source") else None} for img in obj.taxon_images.all()[:5]]
        return []


class TaxonomyTreeSerializer(serializers.Serializer):
    """
    Serializer for taxonomy tree structure.

    Returns hierarchical tree data for visualization.
    """

    id = serializers.IntegerField()
    name = serializers.CharField()
    rank = serializers.CharField()
    children = serializers.SerializerMethodField()
    record_count = serializers.IntegerField(required=False)

    def get_children(self, obj):
        """Recursively serialize children."""
        children = Taxonomy.objects.filter(parent=obj).select_related("parent")
        if not children.exists():
            return []
        return TaxonomyTreeSerializer(children, many=True, context=self.context).data


class TaxonomyCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating/updating taxonomy records.
    """

    parent_id = serializers.PrimaryKeyRelatedField(
        queryset=Taxonomy.objects.all(),
        source="parent",
        write_only=True,
        required=False,
        allow_null=True,
    )
    iucn_status_id = serializers.PrimaryKeyRelatedField(
        queryset=IUCNStatus.objects.all(),
        source="iucn_status",
        write_only=True,
        required=False,
        allow_null=True,
    )
    endemism_id = serializers.PrimaryKeyRelatedField(
        queryset=Endemism.objects.all(),
        source="endemism",
        write_only=True,
        required=False,
        allow_null=True,
    )

    class Meta:
        model = Taxonomy
        fields = [
            "id",
            "scientific_name",
            "canonical_name",
            "rank",
            "taxonomic_status",
            "parent_id",
            "iucn_status_id",
            "endemism_id",
            "gbif_key",
            "author",
            "origin",
            "additional_data",
        ]
        read_only_fields = ["id"]

    def create(self, validated_data):
        """Create taxonomy and set owner."""
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            validated_data["owner"] = request.user
        return super().create(validated_data)
