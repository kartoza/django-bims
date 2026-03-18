# SPDX-FileCopyrightText: Kartoza
# SPDX-License-Identifier: AGPL-3.0
"""
Serializers for BiologicalCollectionRecord model in API v1.
"""
from rest_framework import serializers

from bims.models.biological_collection_record import BiologicalCollectionRecord
from bims.models.location_site import LocationSite
from bims.models.taxonomy import Taxonomy
from bims.models.survey import Survey
from bims.models.source_reference import SourceReference


class BiologicalCollectionRecordListSerializer(serializers.ModelSerializer):
    """
    Serializer for listing biological collection records.

    Provides essential fields for list views.
    """

    site_name = serializers.CharField(source="site.name", read_only=True)
    site_code = serializers.CharField(source="site.site_code", read_only=True)
    taxon_name = serializers.CharField(source="taxonomy.canonical_name", read_only=True)
    taxon_rank = serializers.CharField(source="taxonomy.rank", read_only=True)
    collector_name = serializers.SerializerMethodField()
    coordinates = serializers.SerializerMethodField()

    class Meta:
        model = BiologicalCollectionRecord
        fields = [
            "id",
            "uuid",
            "site_name",
            "site_code",
            "taxon_name",
            "taxon_rank",
            "original_species_name",
            "collection_date",
            "collector_name",
            "abundance_number",
            "present",
            "validated",
            "coordinates",
            "notes",
        ]
        read_only_fields = fields

    def get_collector_name(self, obj):
        """Return collector name from user or string field."""
        if obj.collector_user:
            return f"{obj.collector_user.first_name} {obj.collector_user.last_name}".strip()
        return obj.collector or None

    def get_coordinates(self, obj):
        """Return site coordinates."""
        if obj.site and obj.site.geometry_point:
            return {
                "latitude": round(obj.site.geometry_point.y, 6),
                "longitude": round(obj.site.geometry_point.x, 6),
            }
        return None


class BiologicalCollectionRecordDetailSerializer(BiologicalCollectionRecordListSerializer):
    """
    Detailed serializer for single biological collection record.

    Includes full taxonomy, site, and source reference details.
    """

    site = serializers.SerializerMethodField()
    taxonomy = serializers.SerializerMethodField()
    source_reference = serializers.SerializerMethodField()
    sampling_method = serializers.SerializerMethodField()
    biotope_info = serializers.SerializerMethodField()

    class Meta:
        model = BiologicalCollectionRecord
        fields = BiologicalCollectionRecordListSerializer.Meta.fields + [
            "site",
            "taxonomy",
            "source_reference",
            "sampling_method",
            "sampling_effort",
            "biotope_info",
            "collection_habitat",
            "institution_id",
            "reference",
            "reference_category",
            "source_collection",
            "upstream_id",
            "additional_data",
        ]
        read_only_fields = fields

    def get_site(self, obj):
        """Return site details."""
        if not obj.site:
            return None
        site = obj.site
        return {
            "id": site.id,
            "name": site.name,
            "site_code": site.site_code,
            "ecosystem_type": site.ecosystem_type,
            "coordinates": {
                "latitude": round(site.geometry_point.y, 6) if site.geometry_point else None,
                "longitude": round(site.geometry_point.x, 6) if site.geometry_point else None,
            },
        }

    def get_taxonomy(self, obj):
        """Return taxonomy details."""
        if not obj.taxonomy:
            return None
        tax = obj.taxonomy
        return {
            "id": tax.id,
            "scientific_name": tax.scientific_name,
            "canonical_name": tax.canonical_name,
            "rank": tax.rank,
            "family_name": getattr(tax, "family_name", None),
            "genus_name": getattr(tax, "genus_name", None),
            "species_name": getattr(tax, "species_name", None),
            "iucn_status": tax.iucn_status.category if tax.iucn_status else None,
            "endemism": tax.endemism.name if tax.endemism else None,
        }

    def get_source_reference(self, obj):
        """Return source reference details."""
        if not obj.source_reference:
            return None
        ref = obj.source_reference
        return {
            "id": ref.id,
            "title": getattr(ref, "title", None),
            "authors": getattr(ref, "authors", None),
            "year": getattr(ref, "year", None),
            "reference_type": ref.reference_type,
            "note": ref.note,
        }

    def get_sampling_method(self, obj):
        """Return sampling method details."""
        if not obj.sampling_method:
            return None
        return {
            "id": obj.sampling_method.id,
            "name": obj.sampling_method.sampling_method,
        }

    def get_biotope_info(self, obj):
        """Return biotope information."""
        return {
            "biotope": obj.biotope.name if obj.biotope else None,
            "specific_biotope": obj.specific_biotope.name if obj.specific_biotope else None,
            "substratum": obj.substratum.name if obj.substratum else None,
        }


class BiologicalCollectionRecordCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating/updating biological collection records.
    """

    site_id = serializers.PrimaryKeyRelatedField(
        queryset=LocationSite.objects.all(),
        source="site",
        write_only=True,
    )
    taxonomy_id = serializers.PrimaryKeyRelatedField(
        queryset=Taxonomy.objects.all(),
        source="taxonomy",
        write_only=True,
        required=False,
        allow_null=True,
    )
    survey_id = serializers.PrimaryKeyRelatedField(
        queryset=Survey.objects.all(),
        source="survey",
        write_only=True,
        required=False,
        allow_null=True,
    )
    source_reference_id = serializers.PrimaryKeyRelatedField(
        queryset=SourceReference.objects.all(),
        source="source_reference",
        write_only=True,
        required=False,
        allow_null=True,
    )

    class Meta:
        model = BiologicalCollectionRecord
        fields = [
            "id",
            "uuid",
            "site_id",
            "taxonomy_id",
            "survey_id",
            "source_reference_id",
            "original_species_name",
            "collection_date",
            "collector",
            "abundance_number",
            "present",
            "notes",
            "collection_habitat",
            "institution_id",
            "sampling_effort",
            "reference",
            "reference_category",
            "source_collection",
            "additional_data",
        ]
        read_only_fields = ["id", "uuid"]

    def create(self, validated_data):
        """Create record and set collector user."""
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            validated_data["collector_user"] = request.user
            validated_data["owner"] = request.user
        return super().create(validated_data)


class BiologicalCollectionRecordSummarySerializer(serializers.Serializer):
    """
    Serializer for biological collection record summary statistics.
    """

    total_records = serializers.IntegerField()
    validated_records = serializers.IntegerField()
    pending_records = serializers.IntegerField()
    species_count = serializers.IntegerField()
    site_count = serializers.IntegerField()
    date_range = serializers.DictField()
