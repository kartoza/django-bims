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
    family = serializers.SerializerMethodField()
    accepted_taxonomy_name = serializers.SerializerMethodField()
    accepted_taxonomy_id = serializers.SerializerMethodField()
    biographic_distributions = serializers.SerializerMethodField()
    tag_list = serializers.SerializerMethodField()
    parent_id = serializers.SerializerMethodField()

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
            "author",
            "family",
            "accepted_taxonomy_name",
            "accepted_taxonomy_id",
            "biographic_distributions",
            "tag_list",
            "parent_id",
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

    def get_family(self, obj):
        """Return family name from hierarchy."""
        # Check hierarchical_data first
        if obj.hierarchical_data and isinstance(obj.hierarchical_data, dict):
            family = obj.hierarchical_data.get("family")
            if family:
                return family
        # Fall back to parent traversal
        current = obj
        for _ in range(10):  # Limit traversal depth
            if current.rank and current.rank.upper() == "FAMILY":
                return current.canonical_name or current.scientific_name
            if not current.parent:
                break
            current = current.parent
        return None

    def get_accepted_taxonomy_name(self, obj):
        """Return the canonical name of the accepted taxonomy if this is a synonym."""
        if obj.accepted_taxonomy:
            return obj.accepted_taxonomy.canonical_name or obj.accepted_taxonomy.scientific_name
        return None

    def get_accepted_taxonomy_id(self, obj):
        """Return the ID of the accepted taxonomy if this is a synonym."""
        if obj.accepted_taxonomy:
            return obj.accepted_taxonomy.id
        return None

    def get_biographic_distributions(self, obj):
        """Return comma-separated list of biographic distributions."""
        try:
            distributions = obj.biographic_distributions.all()
            return ", ".join([d.name for d in distributions])
        except Exception:
            return ""

    def get_tag_list(self, obj):
        """Return comma-separated list of tags."""
        try:
            return ", ".join(obj.tags.names())
        except Exception:
            return ""

    def get_parent_id(self, obj):
        """Return parent ID for tree building."""
        return obj.parent_id if obj.parent else None


class TaxonomyDetailSerializer(TaxonomyListSerializer):
    """
    Detailed serializer for single taxonomy record.

    Includes full hierarchical data, tags, and vernacular names.
    """

    parent = serializers.SerializerMethodField()
    vernacular_names = serializers.SerializerMethodField()
    tags = serializers.SerializerMethodField()
    biographic_distributions_detail = serializers.SerializerMethodField()
    hierarchy = serializers.SerializerMethodField()
    images = serializers.SerializerMethodField()
    # Hierarchical rank fields for expanded row view
    kingdom = serializers.SerializerMethodField()
    phylum = serializers.SerializerMethodField()
    class_name = serializers.SerializerMethodField()
    order = serializers.SerializerMethodField()
    subfamily = serializers.SerializerMethodField()
    tribe = serializers.SerializerMethodField()
    subtribe = serializers.SerializerMethodField()
    genus = serializers.SerializerMethodField()
    subgenus = serializers.SerializerMethodField()
    species_name = serializers.SerializerMethodField()
    subspecies = serializers.SerializerMethodField()
    species_group_name = serializers.SerializerMethodField()
    iucn_status_full_name = serializers.SerializerMethodField()

    class Meta:
        model = Taxonomy
        fields = TaxonomyListSerializer.Meta.fields + [
            "parent",
            "vernacular_names",
            "tags",
            "biographic_distributions_detail",
            "hierarchy",
            "images",
            "legacy_canonical_name",
            "origin",
            "additional_data",
            "hierarchical_data",
            "iucn_redlist_id",
            "iucn_data",
            "fada_id",
            # Hierarchical rank fields
            "kingdom",
            "phylum",
            "class_name",
            "order",
            "subfamily",
            "tribe",
            "subtribe",
            "genus",
            "subgenus",
            "species_name",
            "subspecies",
            "species_group_name",
            "iucn_status_full_name",
        ]
        read_only_fields = fields

    def _get_hierarchical_value(self, obj, key):
        """Helper to get value from hierarchical_data or traverse parents."""
        if obj.hierarchical_data and isinstance(obj.hierarchical_data, dict):
            value = obj.hierarchical_data.get(key)
            if value:
                return value
        return None

    def _get_rank_value(self, obj, target_rank):
        """Get value for a specific taxonomic rank by traversing hierarchy."""
        # First check hierarchical_data
        hierarchy_key = target_rank.lower()
        if hierarchy_key == "class":
            hierarchy_key = "class_name"
        value = self._get_hierarchical_value(obj, hierarchy_key)
        if value:
            return value

        # Traverse parents
        current = obj
        for _ in range(15):  # Limit traversal
            if current.rank and current.rank.upper() == target_rank.upper():
                return current.canonical_name or current.scientific_name
            if not current.parent:
                break
            current = current.parent
        return ""

    def get_kingdom(self, obj):
        return self._get_rank_value(obj, "KINGDOM")

    def get_phylum(self, obj):
        return self._get_rank_value(obj, "PHYLUM")

    def get_class_name(self, obj):
        return self._get_rank_value(obj, "CLASS")

    def get_order(self, obj):
        return self._get_rank_value(obj, "ORDER")

    def get_subfamily(self, obj):
        return self._get_rank_value(obj, "SUBFAMILY")

    def get_tribe(self, obj):
        return self._get_rank_value(obj, "TRIBE")

    def get_subtribe(self, obj):
        return self._get_rank_value(obj, "SUBTRIBE")

    def get_genus(self, obj):
        return self._get_rank_value(obj, "GENUS")

    def get_subgenus(self, obj):
        return self._get_rank_value(obj, "SUBGENUS")

    def get_species_name(self, obj):
        return self._get_rank_value(obj, "SPECIES")

    def get_subspecies(self, obj):
        return self._get_rank_value(obj, "SUBSPECIES")

    def get_species_group_name(self, obj):
        if obj.species_group:
            return obj.species_group.name
        return ""

    def get_iucn_status_full_name(self, obj):
        if obj.iucn_status:
            return obj.iucn_status.get_category_display() if hasattr(obj.iucn_status, 'get_category_display') else obj.iucn_status.category
        return "Not evaluated"

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

    def get_biographic_distributions_detail(self, obj):
        """Return biographic distribution tags with details."""
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
