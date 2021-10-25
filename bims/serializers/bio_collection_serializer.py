import json
import uuid
from preferences import preferences
from rest_framework import serializers
from rest_framework_gis.serializers import (
    GeoFeatureModelSerializer, GeometrySerializerMethodField)
from django.contrib.sites.models import Site
from django.urls import reverse
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
from bims.models.algae_data import AlgaeData
from bims.models.survey import SurveyData, SurveyDataValue
from bims.scripts.collection_csv_keys import *  # noqa
from bims.models.location_context_group import LocationContextGroup
from bims.models.taxonomy import Taxonomy
from bims.utils.gbif import get_species
from bims.utils.occurences import get_fields_from_occurrences

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
    site_code = serializers.SerializerMethodField()
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
    gbif_id = serializers.SerializerMethodField()
    dataset_key = serializers.SerializerMethodField()
    occurrence_id = serializers.SerializerMethodField()
    basis_of_record = serializers.SerializerMethodField()
    institution_code = serializers.SerializerMethodField()
    collection_code = serializers.SerializerMethodField()
    catalog_number = serializers.SerializerMethodField()
    identified_by = serializers.SerializerMethodField()
    rights_holder = serializers.SerializerMethodField()
    recorded_by = serializers.SerializerMethodField()

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

    def get_site_code(self, obj):
        return obj.site.site_code

    def get_original_site_code(self, obj):
        return obj.site.legacy_site_code

    def get_river_name(self, obj):
        if obj.site.river:
            return obj.site.river.name
        return 'Unknown'

    def get_site_description(self, obj):
        if obj.site.site_description:
            return obj.site.site_description
        return obj.site.name

    def get_latitude(self, obj):
        lat = obj.site.get_centroid().y
        return lat

    def get_longitude(self, obj):
        lon = obj.site.get_centroid().x
        return lon

    def get_origin(self, obj):
        category = obj.taxonomy.origin.lower()
        if category in Taxonomy.CATEGORY_CHOICES_DICT:
            return ORIGIN[category]
        else:
            if category:
                return category
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
            return obj.source_reference.title
        else:
            return '-'

    def get_taxon(self, obj):
        if obj.taxonomy:
            if obj.taxonomy.canonical_name:
                return obj.taxonomy.canonical_name
        if obj.original_species_name:
            return obj.original_species_name
        return '-'

    def get_class_name(self, obj):
        class_name = obj.taxonomy.class_name
        if class_name:
            return class_name
        return '-'

    def get_phylum(self, obj):
        phylum_name = obj.taxonomy.phylum_name
        if phylum_name:
            return phylum_name
        return '-'

    def get_order(self, obj):
        order_name = obj.taxonomy.order_name
        if order_name:
            return order_name
        return '-'

    def get_family(self, obj):
        family_name = obj.taxonomy.family_name
        if family_name:
            return family_name
        return '-'

    def get_genus(self, obj):
        genus_name = obj.taxonomy.genus_name
        if genus_name:
            return genus_name
        return '-'

    def get_species(self, obj):
        species_name = obj.taxonomy.species_name
        if species_name:
            genus_name = obj.taxonomy.genus_name
            if genus_name:
                species_name = species_name.replace(genus_name, '')
            return species_name.strip()
        return '-'

    def get_kingdom(self, obj):
        kingdom_name = obj.taxonomy.kingdom_name
        if kingdom_name:
            return kingdom_name
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
            return obj.source_reference.authors
        return '-'

    def get_source(self, obj):
        if obj.source_reference:
            if obj.source_reference.source_name:
                return obj.source_reference.source_name
        return '-'

    def get_year(self, obj):
        if obj.source_reference:
            return obj.source_reference.year
        return '-'

    def get_collector_or_owner(self, obj):
        if obj.collector_user:
            return '{first_name} {last_name}'.format(
                first_name=obj.collector_user.first_name,
                last_name=obj.collector_user.last_name
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
            return obj.collector
        try:
            return '{first_name} {last_name}'.format(
                first_name=obj.owner.first_name,
                last_name=obj.owner.last_name
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

    def occurrences_fields(self, obj, field):
        if obj.upstream_id:
            data = get_fields_from_occurrences(obj)
            try:
                return data[field]
            except:  # noqa
                return '-'
        return '-'

    def get_gbif_id(self, obj):
        return self.occurrences_fields(obj, 'gbifID')

    def get_dataset_key(self, obj):
        return self.occurrences_fields(obj, 'datasetKey')

    def get_occurrence_id(self, obj):
        return self.occurrences_fields(obj, 'occurrenceID')

    def get_basis_of_record(self, obj):
        return self.occurrences_fields(obj, 'basisOfRecord')

    def get_institution_code(self, obj):
        return self.occurrences_fields(obj, 'institutionCode')

    def get_collection_code(self, obj):
        return self.occurrences_fields(obj, 'collectionCode')

    def get_catalog_number(self, obj):
        return self.occurrences_fields(obj, 'catalogNumber')

    def get_identified_by(self, obj):
        return self.occurrences_fields(obj, 'identifiedBy')

    def get_rights_holder(self, obj):
        return self.occurrences_fields(obj, 'rightsHolder')

    def get_recorded_by(self, obj):
        return self.occurrences_fields(obj, 'recordedBy')

    class Meta:
        model = BiologicalCollectionRecord
        fields = [
            'uuid',
            'original_river_name',
            'river_name',
            'original_site_code',
            'site_code',
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
            'notes',
            'gbif_id',
            'dataset_key',
            'occurrence_id',
            'basis_of_record',
            'institution_code',
            'collection_code',
            'catalog_number',
            'identified_by',
            'rights_holder',
            'recorded_by',
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
        if 'show_link' in self.context and self.context['show_link']:
            self.context['header'] = ['Link'] + self.context['header']

        is_algae = False
        if instance.module_group:
            is_algae = 'algae' in instance.module_group.name.lower()

        if is_algae:
            algae_keys = [
                'Curation process',
                'Biomass Indicator: Chl A',
                'Biomass Indicator: AFDM',
                'Autotrophic Index (AI)',
            ]

            algae_data = AlgaeData.objects.filter(survey=instance.survey)
            if algae_data.exists():
                algae_data = algae_data[0]
            else:
                algae_data = None

            for algae_key in algae_keys:
                if algae_key not in self.context['header']:
                    self.context['header'].append(algae_key)
                if algae_data:
                    if algae_key == 'Curation process':
                        result[algae_key] = algae_data.curation_process
                    elif algae_key == 'Biomass Indicator: Chl A':
                        result[algae_key] = algae_data.indicator_chl_a
                    elif algae_key == 'Biomass Indicator: AFDM':
                        result[algae_key] = algae_data.indicator_afdm
                    elif algae_key == 'Autotrophic Index (AI)':
                        result[algae_key] = algae_data.ai

        # FBIS ONLY
        if preferences.SiteSetting.default_data_source == 'fbis':
            all_survey_data = [
                'Water Level',
                'Water Turbidity',
                'Embeddedness'
            ]
            for survey_data_key in all_survey_data:
                if survey_data_key not in self.context['header']:
                    self.context['header'].append(survey_data_key)
                survey_data = SurveyData.objects.filter(
                    name__iexact=survey_data_key
                )
                if survey_data.exists():
                    sdv = SurveyDataValue.objects.filter(
                        survey=instance.survey,
                        survey_data=survey_data[0]
                    )
                    if sdv.exists():
                        result[survey_data_key] = (
                            sdv[0].survey_data_option.option
                        )
            chemical_units = {
                TEMP: TEMP,
                CONDUCTIVITY: CONDUCTIVITY,
                PH: PH,
                DISSOLVED_OXYGEN_MG: DISSOLVED_OXYGEN_MG,
                DISSOLVED_OXYGEN_PERCENT: DISSOLVED_OXYGEN_PERCENT,
                TURBIDITY: TURBIDITY,
                DEPTH_M: DEPTH_M,
                NBV: NBV,
                ORTHOPHOSPHATE: ORTHOPHOSPHATE,
                TOT: TOT,
                SILICA: SILICA,
                NH3_N: NH3_N,
                NH4_N: NH4_N,
                NO3_NO2_N: NO3_NO2_N,
                NO2_N: NO2_N,
                NO3_N: NO3_N,
                TIN: TIN,
                CHLA_B: CHLA_B,
                AFDM: AFDM
            }
            for chem_key in chemical_units:
                if chem_key not in self.context['header']:
                    self.context['header'].append(chem_key)
                chem_record = ChemicalRecord.objects.filter(
                    chem__chem_code__iexact=chemical_units[chem_key],
                    survey__site=instance.site,
                    survey__date=instance.collection_date
                )
                if chem_record.exists():
                    result[chem_key] = chem_record[0].value

        else:
            if chem_records_identifier in self.context['chem_records_cached']:
                result.update(
                    self.context[
                        'chem_records_cached'][chem_records_identifier]
                )
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
                self.context[
                    'chem_records_cached'][chem_records_identifier] = (
                    chem_record_data
                )
                result.update(chem_record_data)

        geocontext_keys = (
            preferences.SiteSetting.geocontext_keys.split(',')
        )
        if 'geocontext_groups' not in self.context:
            self.context['geocontext_groups'] = []
            context_groups = (
                LocationContextGroup.objects.filter(
                    geocontext_group_key__in=geocontext_keys
                )
            )
            for context_group in context_groups:
                self.context['header'].append(context_group.name)
                self.context['geocontext_groups'].append({
                    'name': context_group.name,
                    'key': context_group.key
                })

        if 'geocontext_groups' in self.context:
            for _group in self.context['geocontext_groups']:
                _group_name = _group['name']
                _group_key = _group['key']
                result[_group_name] = self.spatial_data(instance, _group_key)

        if 'show_link' in self.context and self.context['show_link']:
            result['Link'] = ''.join(
                [Site.objects.get_current().domain,
                 reverse(
                     'admin:{}_{}_change'.format(
                         instance._meta.app_label,
                         instance._meta.model_name
                     ),
                     args=[instance.id]
                 )])
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


class BioCollectionOneRowWithLinkSerialier(BioCollectionOneRowSerializer):
    pass
