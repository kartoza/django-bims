from rest_framework import serializers
import json
from django.db.models import Q
from bims.models import (
    LocationSite, LocationContext, LocationContextGroup, SourceReference
)
from sass.models import SiteVisitTaxon, SiteVisitBiotopeTaxon, SiteVisit


class FilterHistorySerializer(object):
    context = {}
    ignored_filters = [
        'siteIdOpen',
        'orderBy',
        'modules'
    ]

    def get_filter_history(self, obj):
        filter_history = {}
        filters = self.context['filters']
        for filter_key, filter_value in filters.items():
            if filter_key in self.ignored_filters:
                continue
            if filter_key == 'spatialFilter':
                continue
            if not filter_value:
                continue
            try:
                filter_data = json.loads(filter_value)
                filter_history[filter_key] = filter_data
            except ValueError:
                filter_history[filter_key] = filter_value
        spatial_filters = filters.get('spatialFilter', None)
        if spatial_filters:
            spatial_filters = json.loads(spatial_filters)
            for spatial_filter in spatial_filters:
                # spatial_filters =
                # ['value,primary_catchment,context_value',
                # ['group,primary_catchment']
                filter_values = spatial_filter.split(',')
                if len(filter_values) < 2:
                    continue
                group = LocationContextGroup.objects.filter(
                    key=filter_values[1]
                )
                if not group.exists():
                    continue
                group = group[0]
                if filter_values[0] == 'value' and len(filter_values) > 2:
                    filter_history[group.name] = filter_values[2]
                else:
                    filter_history[group.name] = 'All'
        return filter_history


class SassDataSerializer(serializers.ModelSerializer, FilterHistorySerializer):

    filter_history = serializers.SerializerMethodField()
    original_river_name = serializers.SerializerMethodField()
    FBIS_site_code = serializers.SerializerMethodField()
    original_site_code = serializers.SerializerMethodField()
    site_description = serializers.SerializerMethodField()
    river_name = serializers.SerializerMethodField()
    geomorphological_zone = serializers.SerializerMethodField()
    geomorphological_zone_ground_truthed = serializers.SerializerMethodField()
    latitude = serializers.SerializerMethodField()
    longitude = serializers.SerializerMethodField()
    sampling_date = serializers.SerializerMethodField()
    accredited = serializers.SerializerMethodField()
    sass_version = serializers.SerializerMethodField()
    collector_or_owner = serializers.SerializerMethodField()
    sass_taxa = serializers.SerializerMethodField()
    s = serializers.SerializerMethodField()
    v = serializers.SerializerMethodField()
    g = serializers.SerializerMethodField()
    site = serializers.SerializerMethodField()

    class Meta:
        model = SiteVisitTaxon
        fields = [
            'filter_history',
            'FBIS_site_code',
            'original_river_name',
            'original_site_code',
            'site_description',
            'river_name',
            'geomorphological_zone',
            'geomorphological_zone_ground_truthed',
            'latitude',
            'longitude',
            'sampling_date',
            'accredited',
            'sass_version',
            'collector_or_owner',
            'sass_taxa',
            's',
            'v',
            'g',
            'site'
        ]

    def get_FBIS_site_code(self, obj):
        site_code = obj.site_visit.location_site.site_code
        if not site_code:
            return obj.site_visit.location_site.name
        return site_code

    def get_site_description(self, obj):
        return obj.site_visit.location_site.site_description

    def get_river_name(self, obj):
        if obj.site_visit.location_site.river:
            return obj.site_visit.location_site.river.name
        return '-'

    def get_geomorphological_zone(self, obj):
        site = obj.site_visit.location_site
        if site.original_geomorphological:
            return site.original_geomorphological
        else:
            location_context = LocationContext.objects.filter(
                site=site
            )
            return location_context.value_from_key(
                'geo_class_recoded'
            )

    def get_geomorphological_zone_ground_truthed(self, obj):
        site = obj.site_visit.location_site
        if site.refined_geomorphological:
            return site.refined_geomorphological
        return '-'

    def get_latitude(self, obj):
        return obj.site_visit.location_site.latitude

    def get_longitude(self, obj):
        return obj.site_visit.location_site.longitude

    def get_sampling_date(self, obj):
        return obj.site_visit.site_visit_date

    def get_accredited(self, obj):
        owner = obj.site_visit.owner
        if not owner:
            owner = obj.survey.owner
        try:
            if owner.bims_profile.is_accredited(
                collection_date=obj.site_visit.site_visit_date
            ):
                return 'Y'
            else:
                return 'N'
        except AttributeError:
            return 'N'

    def get_sass_version(self, obj):
        return obj.site_visit.sass_version

    def get_collector_or_owner(self, obj):
        owner = obj.site_visit.owner
        if not owner:
            owner = obj.survey.owner
        try:
            return owner.username
        except AttributeError:
            return '-'

    def get_sass_taxa(self, obj):
        if obj.sass_taxon.taxon_sass_4:
            return obj.sass_taxon.taxon_sass_4
        elif obj.sass_taxon.taxon_sass_5:
            return obj.sass_taxon.taxon_sass_5
        else:
            return obj.sass_taxon.taxon

    def get_weight(self, obj):
        if obj.site_visit.sass_version == 4:
            return obj.sass_taxon.score
        else:
            return obj.sass_taxon.sass_5_score

    def get_s(self, obj):
        site_visit_biotope = (
            SiteVisitBiotopeTaxon.objects.filter(
                Q(biotope__name__icontains='sic') |
                Q(biotope__name__icontains='sooc'),
                site_visit=obj.site_visit,
                sass_taxon=obj.sass_taxon,
            )
        )
        if not site_visit_biotope.exists():
            return ''
        try:
            return site_visit_biotope.first().taxon_abundance.abc
        except AttributeError:
            return ''

    def get_v(self, obj):
        site_visit_biotope = (
            SiteVisitBiotopeTaxon.objects.filter(
                Q(biotope__name__icontains='vegetation') |
                Q(biotope__name__icontains='mv/aqv'),
                site_visit=obj.site_visit,
                sass_taxon=obj.sass_taxon,
            )
        )
        if not site_visit_biotope.exists():
            return ''
        try:
            return site_visit_biotope.first().taxon_abundance.abc
        except AttributeError:
            return ''

    def get_g(self, obj):
        site_visit_biotope = (
            SiteVisitBiotopeTaxon.objects.filter(
                Q(biotope__name__icontains='gravel') |
                Q(biotope__name__icontains='sand') |
                Q(biotope__name__icontains='mud') |
                Q(biotope__name__icontains='g/s/m'),
                site_visit=obj.site_visit,
                sass_taxon=obj.sass_taxon,
            )
        )
        if not site_visit_biotope.exists():
            return ''
        try:
            return site_visit_biotope.first().taxon_abundance.abc
        except AttributeError:
            return ''

    def get_site(self, obj):
        if obj.taxon_abundance:
            return obj.taxon_abundance.abc
        return ''

    def get_original_river_name(self, obj):
        if obj.site_visit.location_site.legacy_river_name:
            return obj.site_visit.location_site.legacy_river_name
        return '-'

    def get_original_site_code(self, obj):
        if obj.site_visit.location_site.legacy_site_code:
            return obj.site_visit.location_site.legacy_site_code
        return '-'



class SassSummaryDataSerializer(
    serializers.ModelSerializer, FilterHistorySerializer):

    filter_history = serializers.SerializerMethodField()
    original_river_name = serializers.SerializerMethodField()
    FBIS_site_code = serializers.SerializerMethodField()
    original_site_code = serializers.SerializerMethodField()
    sass_score = serializers.SerializerMethodField()
    number_of_taxa = serializers.SerializerMethodField()
    ASPT = serializers.SerializerMethodField()
    sampling_date = serializers.SerializerMethodField()
    owner = serializers.SerializerMethodField()
    sass_version = serializers.SerializerMethodField()
    site_description = serializers.SerializerMethodField()
    river_name = serializers.SerializerMethodField()
    latitude = serializers.SerializerMethodField()
    longitude = serializers.SerializerMethodField()
    reference_category = serializers.SerializerMethodField()
    study_reference = serializers.SerializerMethodField()
    accredited = serializers.SerializerMethodField()
    geomorphological_zone = serializers.SerializerMethodField()
    refined_geomorphological_zone = serializers.SerializerMethodField()
    ecological_category = serializers.SerializerMethodField()
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
            site=obj['site_id'],
            key=key)
        if context_identifier in self.context['context_cache']:
            return self.context['context_cache'][context_identifier]
        data = (
            self.context['location_contexts'].filter(
                site_id=obj['site_id'],
                group__key__icontains=key)
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

    def get_source_reference(self, obj):
        if 'source_reference' not in self.context:
            self.context['source_reference'] = {}
        identifier = obj['source_reference']
        try:
            self.context['source_reference'][identifier] = (
                SourceReference.objects.get(
                    id=obj['source_reference']
                )
            )
        except SourceReference.DoesNotExist:
            return ''
        return identifier

    def get_accredited(self, obj):
        site_visit = SiteVisit.objects.get(id=obj['sass_id'])
        owner = site_visit.owner
        try:
            if not owner:
                return 'N'
            if owner.bims_profile.is_accredited(
                collection_date=site_visit.site_visit_date
            ):
                return 'Y'
            else:
                return 'N'
        except:  # noqa
            return 'N'

    def get_ecological_category(self, obj):
        return obj['ecological_category']

    def get_reference_category(self, obj):
        identifier = ''
        reference_category = '-'
        if obj['source_reference']:
            identifier = self.get_source_reference(obj)
        if identifier and self.context['source_reference'][identifier]:
            reference_category = (
              self.context['source_reference'][identifier].reference_type
            )
        else:
            if self.context['default_source_reference']:
                reference_category = (
                    self.context['default_source_reference'].reference_type
                )
        return reference_category

    def get_study_reference(self, obj):
        identifier = ''
        study_reference = '-'
        if obj['source_reference']:
            identifier = self.get_source_reference(obj)
        if identifier and self.context['source_reference'][identifier]:
            study_reference = str(
                self.context['source_reference'][identifier].title
            )
        else:
            if self.context['default_source_reference']:
                study_reference = (
                    self.context['default_source_reference'].title
                )
        return study_reference

    def get_river_name(self, obj):
        return obj['river_name']

    def get_latitude(self, obj):
        return obj['latitude']

    def get_longitude(self, obj):
        return obj['longitude']

    def get_site_description(self, obj):
        return obj['site_description']

    def get_FBIS_site_code(self, obj):
        return obj['FBIS_site_code']

    def get_owner(self, obj):
        site_visit = SiteVisit.objects.get(id=obj['sass_id'])
        owner = site_visit.owner
        if owner:
            return '{} {}'.format(
                owner.first_name,
                owner.last_name
            )
        return '-'

    def get_sass_version(self, obj):
        return obj['sass_version']

    def get_sass_score(self, obj):
        return obj['sass_score']

    def get_number_of_taxa(self, obj):
        return obj['count']

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

    def get_ASPT(self, obj):
        return '{0:.2f}'.format(obj['aspt'])

    def get_sampling_date(self, obj):
        site_visit_date = obj['sampling_date']
        return site_visit_date.strftime('%Y-%m-%d')

    def get_geomorphological_zone(self, obj):
        site = LocationSite.objects.get(id=obj['site_id'])
        if site.original_geomorphological:
            return site.original_geomorphological
        else:
            location_context = LocationContext.objects.filter(
                site=site
            )
            return location_context.value_from_key(
                'geo_class_recoded'
            )

    def get_refined_geomorphological_zone(self, obj):
        site = LocationSite.objects.get(id=obj['site_id'])
        if site.refined_geomorphological:
            return site.refined_geomorphological
        return '-'

    def get_original_river_name(self, obj):
        site = LocationSite.objects.get(id=obj['site_id'])
        if site.legacy_river_name:
            return site.legacy_river_name
        return '-'

    def get_original_site_code(self, obj):
        site = LocationSite.objects.get(id=obj['site_id'])
        if site.legacy_site_code:
            return site.legacy_site_code
        return '-'

    def group_fields(self, context_key, site_id, result):
        try:
            location_site = LocationSite.objects.get(
                id=site_id
            )
        except LocationSite.DoesNotExist:
            return ''
        location_context = LocationContext.objects.filter(
            site=location_site
        )
        for context in location_context:
            result[context.name] = context.value
        return result

    class Meta:
        model = SiteVisitTaxon
        fields = [
            'filter_history',
            'FBIS_site_code',
            'original_river_name',
            'original_site_code',
            'site_description',
            'river_name',
            'geomorphological_zone',
            'refined_geomorphological_zone',
            'latitude',
            'longitude',
            'sampling_date',
            'accredited',
            'sass_version',
            'sass_score',
            'number_of_taxa',
            'ASPT',
            'ecological_category',
            'reference_category',
            'study_reference',
            'owner',
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
            'province'
        ]

    def biotope_fractions(self, site_visit_id, result):
        try:
            site_visit = SiteVisit.objects.get(id=site_visit_id)
        except SiteVisit.DoesNotExist:
            return result
        biotope_fractions = site_visit.sass_biotope_fraction.all()
        biotopes_needed = [
            'Stones in current',
            'Stones out of current',
            'Aquatic vegetation',
            'Marginal vegetation in current',
            'Marginal vegetation out of current',
            'Gravel',
            'Sand',
            'Mud'
        ]
        for biotope in biotopes_needed:
            biotope_rate = '-'
            fractions = biotope_fractions.filter(
                sass_biotope__name__icontains=biotope
            )
            if fractions.exists():
                fraction = fractions[0]
                if fraction.rate:
                    biotope_rate = fraction.rate.description
            result[biotope] = biotope_rate
        return result

    def to_representation(self, obj):
        result = super(SassSummaryDataSerializer, self).to_representation(obj)
        site_visit_id = obj['sass_id']
        result = self.biotope_fractions(site_visit_id, result)
        return result
