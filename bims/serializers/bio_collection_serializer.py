import json
import uuid
from rest_framework import serializers
from rest_framework_gis.serializers import (
    GeoFeatureModelSerializer, GeometrySerializerMethodField)
from django.contrib.sites.models import Site
from bims.models.biological_collection_record import BiologicalCollectionRecord
from bims.serializers.taxon_serializer import (
    TaxonSerializer,
    TaxonExportSerializer
)
from bims.models.source_reference import (
    SourceReferenceBibliography,
    SourceReferenceDocument,
    SourceReferenceDatabase
)
from bims.models.chemical_record import (
    ChemicalRecord
)
from bims.models.iucn_status import IUCNStatus
from bims.models.location_context import LocationContext

ORIGIN = {
    'alien': 'Non-Native',
    'indigenous': 'Native',
}


class BioCollectionSerializer(serializers.ModelSerializer):
    """
    Serializer for biological collection record.
    """
    location = serializers.SerializerMethodField()
    owner = serializers.SerializerMethodField()
    owner_email = serializers.SerializerMethodField()
    taxonomy = serializers.SerializerMethodField()
    site_name = serializers.SerializerMethodField()

    def get_site_name(self, obj):
        return obj.site.name

    def get_taxonomy(self, obj):
        return TaxonSerializer(obj.taxonomy).data

    def get_owner(self, obj):
        return obj.owner.username

    def get_owner_email(self, obj):
        return obj.owner.email

    def get_location(self, obj):
        return obj.site.get_geometry().geojson

    class Meta:
        model = BiologicalCollectionRecord
        fields = '__all__'


class BioCollectionOneRowSerializer(serializers.ModelSerializer):
    """
    Serializer for biological collection record.
    """
    uuid = serializers.SerializerMethodField()
    original_river_name = serializers.SerializerMethodField()
    fbis_site_code = serializers.SerializerMethodField()
    original_site_code = serializers.SerializerMethodField()
    site_description = serializers.SerializerMethodField()
    refined_geomorphological_zone = serializers.SerializerMethodField()
    river_name = serializers.SerializerMethodField()
    latitude = serializers.SerializerMethodField()
    longitude = serializers.SerializerMethodField()
    origin = serializers.SerializerMethodField()
    sampling_date = serializers.SerializerMethodField()
    sampling_method = serializers.SerializerMethodField()
    broad_biotope = serializers.SerializerMethodField()
    specific_biotope = serializers.SerializerMethodField()
    substratum = serializers.SerializerMethodField()
    taxon = serializers.SerializerMethodField()
    collector_or_owner = serializers.SerializerMethodField()
    title = serializers.SerializerMethodField()
    reference_category = serializers.SerializerMethodField()
    endemism = serializers.SerializerMethodField()
    conservation_status = serializers.SerializerMethodField()
    phylum = serializers.SerializerMethodField()
    class_name = serializers.SerializerMethodField()
    order = serializers.SerializerMethodField()
    family = serializers.SerializerMethodField()
    genus = serializers.SerializerMethodField()
    kingdom = serializers.SerializerMethodField()
    taxon_rank = serializers.SerializerMethodField()
    species = serializers.SerializerMethodField()
    notes = serializers.SerializerMethodField()
    doi_or_url = serializers.SerializerMethodField()
    sampling_effort_measure = serializers.SerializerMethodField()
    sampling_effort_value = serializers.SerializerMethodField()
    abundance_measure = serializers.SerializerMethodField()
    abundance_value = serializers.SerializerMethodField()
    collector_or_owner_institute = serializers.SerializerMethodField()
    analyst = serializers.SerializerMethodField()
    analyst_institute = serializers.SerializerMethodField()
    authors = serializers.SerializerMethodField()
    source = serializers.SerializerMethodField()
    year = serializers.SerializerMethodField()
    geomorphological_zone = serializers.SerializerMethodField()
    primary_catchment = serializers.SerializerMethodField()
    secondary_catchment = serializers.SerializerMethodField()
    tertiary_catchment = serializers.SerializerMethodField()
    quaternary_catchment = serializers.SerializerMethodField()
    water_management_area = serializers.SerializerMethodField()
    sub_water_management_area = serializers.SerializerMethodField()
    river_management_unit = serializers.SerializerMethodField()
    sa_ecoregion_level_1 = serializers.SerializerMethodField()
    sa_ecoregion_level_2 = serializers.SerializerMethodField()
    freshwater_ecoregion = serializers.SerializerMethodField()
    province = serializers.SerializerMethodField()

    def spatial_data(self, obj, key):
        if 'context_cache' not in self.context:
            self.context['context_cache'] = {}
        context_identifier = '{key}-{site}'.format(
            site=obj.site.id,
            key=key)
        if context_identifier in self.context['context_cache']:
            return self.context['context_cache'][context_identifier]
        data = (
            LocationContext.objects.filter(
                site_id=obj.site.id,
                group__key__icontains=key).exclude(
                value=''
            )
        )
        if data.exists():
            if data[0].value:
                self.context['context_cache'][context_identifier] = (
                    data[0].value
                )
                return data[0].value
        self.context['context_cache'][context_identifier] = (
            '-'
        )
        return '-'

    def __init__(self, *args, **kwargs):
        super(BioCollectionOneRowSerializer, self).__init__(*args, **kwargs)
        self.context['chem_records_cached'] = {}
        self.context['header'] = []

    def chem_data(self, obj, chem):
        return chem

    def get_abundance_measure(self, obj):
        if obj.abundance_type:
            return obj.get_abundance_type_display()
        return '-'

    def get_abundance_value(self, obj):
        if obj.abundance_number:
            return obj.abundance_number
        return '-'

    def get_uuid(self, obj):
        if obj.uuid:
            return str(uuid.UUID(obj.uuid))
        return '-'

    def get_original_river_name(self, obj):
        if obj.site.legacy_river_name:
            return obj.site.legacy_river_name
        return '-'

    def get_refined_geomorphological_zone(self, obj):
        if obj.site.refined_geomorphological:
            return obj.site.refined_geomorphological
        return '-'

    def get_geomorphological_zone(self, obj):
        return self.spatial_data(obj, 'geo_class_recoded')

    def get_primary_catchment(self, obj):
        return self.spatial_data(obj, 'primary_catchment_area')

    def get_secondary_catchment(self, obj):
        return self.spatial_data(obj, 'secondary_catchment_area')

    def get_tertiary_catchment(self, obj):
        return self.spatial_data(obj, 'tertiary_catchment_area')

    def get_quaternary_catchment(self, obj):
        return self.spatial_data(obj, 'quaternary_catchment_area')

    def get_water_management_area(self, obj):
        return self.spatial_data(obj, 'water_management_area')

    def get_sub_water_management_area(self, obj):
        return self.spatial_data(obj, 'sub_wmas')

    def get_river_management_unit(self, obj):
        return self.spatial_data(obj, 'river_management_unit')

    def get_sa_ecoregion_level_1(self, obj):
        return self.spatial_data(obj, 'eco_region_1')

    def get_sa_ecoregion_level_2(self, obj):
        return self.spatial_data(obj, 'eco_region_2')

    def get_freshwater_ecoregion(self, obj):
        return self.spatial_data(obj, 'feow_hydrosheds')

    def get_province(self, obj):
        return self.spatial_data(obj, 'sa_provinces')

    def get_sampling_effort_measure(self, obj):
        if obj.sampling_effort:
            return ' '.join(obj.sampling_effort.split(' ')[1:])
        return '-'

    def get_sampling_effort_value(self, obj):
        if obj.sampling_effort:
            return obj.sampling_effort.split(' ')[0]
        return '-'

    def get_conservation_status(self, obj):
        if obj.taxonomy.iucn_status:
            category = dict(IUCNStatus.CATEGORY_CHOICES)
            try:
                return category[obj.taxonomy.iucn_status.category]
            except KeyError:
                pass
        return 'Not evaluated'

    def get_fbis_site_code(self, obj):
        return obj.site.site_code

    def get_original_site_code(self, obj):
        return obj.site.legacy_site_code

    def get_river_name(self, obj):
        if obj.site.river:
            return obj.site.river.name
        return 'Unknown'

    def get_site_description(self, obj):
        if obj.site.site_description:
            return obj.site.site_description.encode('utf8')
        return obj.site.name.encode('utf8')

    def get_latitude(self, obj):
        lat = obj.site.get_centroid().y
        return lat

    def get_longitude(self, obj):
        lon = obj.site.get_centroid().x
        return lon

    def get_origin(self, obj):
        category = obj.category
        if category in ORIGIN:
            return ORIGIN[category]
        else:
            return 'Unknown'

    def get_endemism(self, obj):
        if obj.taxonomy.endemism:
            return obj.taxonomy.endemism.name
        return 'Unknown'

    def get_sampling_date(self, obj):
        if obj.collection_date:
            return obj.collection_date.isoformat().split('T')[0]

    def get_title(self, obj):
        if obj.source_reference:
            return obj.source_reference.title.encode('utf-8')
        else:
            return '-'

    def get_taxon(self, obj):
        if obj.original_species_name:
            return obj.original_species_name.encode('utf-8')
        return '-'

    def get_class_name(self, obj):
        class_name = obj.taxonomy.class_name
        if class_name:
            return class_name.encode('utf-8')
        return '-'

    def get_phylum(self, obj):
        phylum_name = obj.taxonomy.phylum_name
        if phylum_name:
            return phylum_name.encode('utf-8')
        return '-'

    def get_order(self, obj):
        order_name = obj.taxonomy.order_name
        if order_name:
            return order_name.encode('utf-8')
        return '-'

    def get_family(self, obj):
        family_name = obj.taxonomy.family_name
        if family_name:
            return family_name.encode('utf-8')
        return '-'

    def get_genus(self, obj):
        genus_name = obj.taxonomy.genus_name
        if genus_name:
            return genus_name.encode('utf-8')
        return '-'

    def get_species(self, obj):
        species_name = obj.taxonomy.species_name
        if species_name:
            genus_name = obj.taxonomy.genus_name
            if genus_name:
                species_name = species_name.replace(genus_name, '')
            return species_name.encode('utf-8').strip()
        return '-'

    def get_kingdom(self, obj):
        kingdom_name = obj.taxonomy.kingdom_name
        if kingdom_name:
            return kingdom_name.encode('utf-8')
        return '-'

    def get_taxon_rank(self, obj):
        taxon_rank = obj.taxonomy.get_rank_display()
        return taxon_rank if taxon_rank else '-'

    def get_reference_category(self, obj):
        if obj.source_reference:
            return obj.source_reference.reference_type
        else:
            return '-'

    def get_authors(self, obj):
        if obj.source_reference:
            return obj.source_reference.authors.encode('utf-8')
        return '-'

    def get_source(self, obj):
        if obj.source_reference:
            if obj.source_reference.source_name:
                return obj.source_reference.source_name.encode('utf-8')
        return '-'

    def get_year(self, obj):
        if obj.source_reference:
            return obj.source_reference.year
        return '-'

    def get_collector_or_owner(self, obj):
        if obj.collector_user:
            return '{first_name} {last_name}'.format(
                first_name=obj.collector_user.first_name.encode('utf-8'),
                last_name=obj.collector_user.last_name.encode('utf-8')
            )
        if obj.additional_data:
            # If this is BioBase data, return a collector name from author of
            # reference
            additional_data = {}
            if isinstance(obj.additional_data, str):
                additional_data = json.loads(obj.additional_data)
            elif isinstance(obj.additional_data, dict):
                additional_data = obj.additional_data
            if 'BioBaseData' in additional_data:
                if isinstance(
                        obj.source_reference, SourceReferenceBibliography):
                    source = obj.source_reference.source
                    author_str = '%(last_name)s %(first_initial)s'
                    s = ', '.join(
                        [author_str % a.__dict__ for a in
                         source.get_authors()])
                    s = ', and '.join(s.rsplit(', ', 1))  # last author case
                    return s
        if obj.collector:
            return obj.collector.encode('utf8')
        try:
            return '{first_name} {last_name}'.format(
                first_name=obj.owner.first_name.encode('utf-8'),
                last_name=obj.owner.last_name.encode('utf-8')
            )
        except Exception as e:  # noqa
            return '-'

    def get_collector_or_owner_institute(self, obj):
        if obj.collector_user:
            if obj.collector_user.organization:
                return obj.collector_user.organization
        return '-'

    def get_analyst(self, obj):
        if obj.analyst:
            return '{first_name} {last_name}'.format(
                first_name=obj.analyst.first_name,
                last_name=obj.analyst.last_name
            )
        return '-'

    def get_analyst_institute(self, obj):
        if obj.analyst:
            return obj.analyst.organization
        return '-'

    def get_notes(self, obj):
        return obj.notes

    def get_doi_or_url(self, obj):
        if obj.source_reference:
            url = ''
            document = None
            if isinstance(obj.source_reference,
                          SourceReferenceBibliography):
                url = obj.source_reference.source.doi
                if not url and obj.source_reference.document:
                    document = obj.source_reference.document
            elif isinstance(obj.source_reference,
                            SourceReferenceDocument):
                document = obj.source_reference.source
            elif isinstance(obj.source_reference,
                            SourceReferenceDatabase):
                if obj.source_reference.document:
                    document = obj.source_reference.document
            if not url and document:
                if document.doc_file:
                    url = ''.join(
                        [Site.objects.get_current().domain,
                         document.doc_file.url])
                else:
                    url = document.doc_url
            return url
        return '-'

    def get_sampling_method(self, obj):
        if obj.sampling_method:
            return obj.sampling_method.sampling_method.capitalize()
        return obj.sampling_method_string

    def get_broad_biotope(self, obj):
        if obj.biotope:
            return obj.biotope.name.capitalize()
        return '-'

    def get_specific_biotope(self, obj):
        if obj.specific_biotope:
            return obj.specific_biotope.name.capitalize()
        return '-'

    def get_substratum(self, obj):
        if obj.substratum:
            return obj.substratum.name.capitalize()
        return '-'

    class Meta:
        model = BiologicalCollectionRecord
        fields = [
            'uuid',
            'original_river_name',
            'river_name',
            'original_site_code',
            'fbis_site_code',
            'site_description',
            'refined_geomorphological_zone',
            'latitude',
            'longitude',
            'sampling_date',
            'kingdom',
            'phylum',
            'class_name',
            'order',
            'family',
            'genus',
            'species',
            'taxon',
            'taxon_rank',
            'sampling_method',
            'sampling_effort_measure',
            'sampling_effort_value',
            'abundance_measure',
            'abundance_value',
            'broad_biotope',
            'specific_biotope',
            'substratum',
            'origin',
            'endemism',
            'conservation_status',
            'collector_or_owner',
            'collector_or_owner_institute',
            'analyst',
            'analyst_institute',
            'authors',
            'year',
            'source',
            'reference_category',
            'title',
            'doi_or_url',
            'geomorphological_zone',
            'primary_catchment',
            'secondary_catchment',
            'tertiary_catchment',
            'quaternary_catchment',
            'water_management_area',
            'sub_water_management_area',
            'river_management_unit',
            'sa_ecoregion_level_1',
            'sa_ecoregion_level_2',
            'freshwater_ecoregion',
            'province',
            'notes',
        ]

    def to_representation(self, instance):
        result = super(
            BioCollectionOneRowSerializer, self).to_representation(
            instance)
        chem_records_identifier = (
            '{site}-{date}'.format(
                site=instance.site,
                date=instance.collection_date
            )
        )
        if 'chem_records_cached' not in self.context:
            self.context['chem_records_cached'] = {}
        if 'header' not in self.context:
            self.context['header'] = list(result.keys())
        if chem_records_identifier in self.context['chem_records_cached']:
            result.update(
                self.context['chem_records_cached'][chem_records_identifier])
        else:
            chem_record_data = {}
            chem_records = ChemicalRecord.objects.filter(
                survey__site=instance.site,
                survey__date=instance.collection_date
            ).distinct('chem__chem_code')
            for chem_record in chem_records:
                chem_code = chem_record.chem.chem_code.upper()
                if chem_code not in self.context['header']:
                    self.context['header'].append(chem_code)
                chem_record_data[chem_code] = chem_record.value
            self.context['chem_records_cached'][chem_records_identifier] = (
                chem_record_data
            )
            result.update(chem_record_data)
        return result


class BioCollectionGeojsonSerializer(GeoFeatureModelSerializer):
    geometry = GeometrySerializerMethodField()
    location_site = serializers.SerializerMethodField()
    species_name = serializers.SerializerMethodField()
    notes = serializers.SerializerMethodField()
    category = serializers.SerializerMethodField()
    date = serializers.SerializerMethodField()
    collector = serializers.SerializerMethodField()

    def get_location_site(self, obj):
        if obj.site:
            return obj.site.name
        return ''

    def get_species_name(self, obj):
        return obj.original_species_name

    def get_notes(self, obj):
        return obj.notes

    def get_category(self, obj):
        return obj.category

    def get_date(self, obj):
        if obj.collection_date:
            return obj.collection_date.isoformat().split('T')[0]

    def get_collector(self, obj):
        return obj.collector

    def get_geometry(self, obj):
        if obj.site:
            return obj.site.get_geometry()
        return None

    class Meta:
        model = BiologicalCollectionRecord
        geo_field = 'geometry'
        fields = [
            'location_site', 'species_name', 'notes', 'category',
            'date', 'collector']

    def to_representation(self, instance):
        result = super(
            BioCollectionGeojsonSerializer, self).to_representation(
            instance)
        try:
            taxonomy = TaxonExportSerializer(instance.taxonomy).data
            result['properties'].update(taxonomy)
        except KeyError:
            pass
        return result
