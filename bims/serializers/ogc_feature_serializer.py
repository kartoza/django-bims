# coding=utf-8
"""GeoJSON Feature serialization for the OGC API - Features endpoints.

Builds a flat, GIS-client friendly property list for a
BiologicalCollectionRecord, as served by an OgcLayer.
"""
import json

from rest_framework import serializers

from bims.enums.taxonomic_rank import TaxonomicRank


class OgcFeaturePropertiesSerializer(serializers.Serializer):
    """Flat property list for a BiologicalCollectionRecord OGC feature."""

    record_id = serializers.IntegerField(source='pk')
    uuid = serializers.SerializerMethodField()
    species_name = serializers.SerializerMethodField()
    taxon_rank = serializers.SerializerMethodField()
    site_code = serializers.SerializerMethodField()
    date = serializers.SerializerMethodField()
    collector = serializers.SerializerMethodField()
    owner = serializers.SerializerMethodField()
    institution = serializers.SerializerMethodField()
    validation_status = serializers.SerializerMethodField()
    origin = serializers.SerializerMethodField()
    conservation_status = serializers.SerializerMethodField()

    @staticmethod
    def _person_name(user):
        if not user:
            return None
        full_name = ('%s %s' % (user.first_name, user.last_name)).strip()
        return full_name or user.username

    def get_uuid(self, obj):
        return str(obj.uuid) if obj.uuid else None

    def get_species_name(self, obj):
        taxonomy = obj.taxonomy
        if taxonomy and taxonomy.canonical_name:
            return taxonomy.canonical_name
        return obj.original_species_name

    def get_taxon_rank(self, obj):
        taxonomy = obj.taxonomy
        if not taxonomy or not taxonomy.rank:
            return None
        try:
            return TaxonomicRank[taxonomy.rank].value
        except KeyError:
            return taxonomy.rank

    def get_site_code(self, obj):
        site = obj.site
        if not site:
            return None
        return site.site_code or site.legacy_site_code

    def get_date(self, obj):
        if not obj.collection_date:
            return None
        return obj.collection_date.isoformat()

    def get_collector(self, obj):
        return obj.collector or self._person_name(obj.collector_user)

    def get_owner(self, obj):
        return self._person_name(obj.owner)

    def get_institution(self, obj):
        return obj.institution_id or None

    def get_validation_status(self, obj):
        if obj.ready_for_validation:
            return 'in_review'
        if obj.is_validated:
            return 'validated'
        if obj.is_rejected:
            return 'rejected'
        return 'unvalidated'

    def get_origin(self, obj):
        taxonomy = obj.taxonomy
        if taxonomy and taxonomy.origin:
            return taxonomy.origin.category
        return None

    def get_conservation_status(self, obj):
        taxonomy = obj.taxonomy
        if not taxonomy:
            return None
        status = taxonomy.iucn_status or taxonomy.national_conservation_status
        if not status and taxonomy.accepted_taxonomy:
            status = taxonomy.accepted_taxonomy.iucn_status
        if not status:
            return None
        return status.get_status()


def feature_geometry(record):
    site = record.site
    if not site:
        return None
    geometry = site.get_geometry()
    if geometry is None:
        return None
    return json.loads(geometry.geojson)


def feature_from_record(record, properties=None):
    """Return a GeoJSON Feature dict for a BiologicalCollectionRecord.

    The feature id is the record uuid.

    :param properties: the serialized properties, if already known. See
        features_from_records().
    """
    if properties is None:
        properties = OgcFeaturePropertiesSerializer(record).data
    return {
        'type': 'Feature',
        'id': str(record.uuid) if record.uuid else record.pk,
        'geometry': feature_geometry(record),
        'properties': properties,
    }


def features_from_records(records):
    """Return a GeoJSON Feature dict for each record, lazily.

    Serializing the properties of all records together builds the
    serializer fields once instead of once per record, which is much
    faster for a page of features.
    """
    records = list(records)
    properties = OgcFeaturePropertiesSerializer(records, many=True).data
    for record, props in zip(records, properties):
        yield feature_from_record(record, props)
