# SPDX-FileCopyrightText: Kartoza
# SPDX-License-Identifier: AGPL-3.0
"""
Serializers for Survey model in API v1.
"""
from rest_framework import serializers

from bims.models.survey import Survey
from bims.models.location_site import LocationSite


class SurveyListSerializer(serializers.ModelSerializer):
    """
    Serializer for listing surveys.
    """

    site_name = serializers.CharField(source="site.name", read_only=True)
    site_code = serializers.CharField(source="site.site_code", read_only=True)
    record_count = serializers.SerializerMethodField()
    validation_status = serializers.SerializerMethodField()

    class Meta:
        model = Survey
        fields = [
            "id",
            "uuid",
            "site_name",
            "site_code",
            "date",
            "collector_string",
            "record_count",
            "validation_status",
            "validated",
            "created",
            "modified",
        ]
        read_only_fields = fields

    def get_record_count(self, obj):
        """Return count of biological records in this survey."""
        if hasattr(obj, "record_count"):
            return obj.record_count
        return obj.biological_collection_record.count()

    def get_validation_status(self, obj):
        """Return the validation status of the survey."""
        return obj.validation_status


class SurveyDetailSerializer(SurveyListSerializer):
    """
    Detailed serializer for single survey.
    """

    site = serializers.SerializerMethodField()
    collector_user = serializers.SerializerMethodField()
    records_summary = serializers.SerializerMethodField()

    class Meta:
        model = Survey
        fields = SurveyListSerializer.Meta.fields + [
            "site",
            "collector_user",
            "records_summary",
            "owner",
        ]
        read_only_fields = fields

    def get_site(self, obj):
        """Return site details."""
        if not obj.site:
            return None
        return {
            "id": obj.site.id,
            "name": obj.site.name,
            "site_code": obj.site.site_code,
            "coordinates": {
                "latitude": round(obj.site.geometry_point.y, 6) if obj.site.geometry_point else None,
                "longitude": round(obj.site.geometry_point.x, 6) if obj.site.geometry_point else None,
            },
        }

    def get_collector_user(self, obj):
        """Return collector user details."""
        if obj.collector_user:
            return {
                "id": obj.collector_user.id,
                "username": obj.collector_user.username,
                "full_name": f"{obj.collector_user.first_name} {obj.collector_user.last_name}".strip(),
            }
        return None

    def get_records_summary(self, obj):
        """Return summary of records in this survey."""
        records = obj.biological_collection_record.all()
        return {
            "total": records.count(),
            "validated": records.filter(validated=True).count(),
            "species_count": records.values("taxonomy").distinct().count(),
        }


class SurveyCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating/updating surveys.
    """

    site_id = serializers.PrimaryKeyRelatedField(
        queryset=LocationSite.objects.all(),
        source="site",
        write_only=True,
    )

    class Meta:
        model = Survey
        fields = [
            "id",
            "uuid",
            "site_id",
            "date",
            "collector_string",
        ]
        read_only_fields = ["id", "uuid"]

    def create(self, validated_data):
        """Create survey and set owner/collector."""
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            validated_data["owner"] = request.user
            validated_data["collector_user"] = request.user
        return super().create(validated_data)
