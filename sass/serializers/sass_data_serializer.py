from rest_framework import serializers
import json
from django.db.models import Q
from bims.models import (
    LocationSite, LocationContext, LocationContextGroup
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
    FBIS_site_code = serializers.SerializerMethodField()
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
            try:
                context = json.loads(site.location_context)
                geo = context[
                    'context_group_values'][
                    'geomorphological_group']['service_registry_values'][
                    'geo_class_recoded']['value']
                return geo
            except (KeyError, ValueError):
                return '-'

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
        if obj.site_visit.owner.bims_profile.is_accredited():
            return 'Y'
        else:
            return 'N'

    def get_sass_version(self, obj):
        return obj.site_visit.sass_version

    def get_collector_or_owner(self, obj):
        return obj.site_visit.owner.username

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
        if len(site_visit_biotope) > 0:
            return site_visit_biotope[0].taxon_abundance.abc
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
        if len(site_visit_biotope) > 0:
            return site_visit_biotope[0].taxon_abundance.abc
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
        if len(site_visit_biotope) > 0:
            return site_visit_biotope[0].taxon_abundance.abc
        return ''

    def get_site(self, obj):
        if obj.taxon_abundance:
            return obj.taxon_abundance.abc
        return ''


class SassSummaryDataSerializer(
    serializers.ModelSerializer, FilterHistorySerializer):

    filter_history = serializers.SerializerMethodField()
    FBIS_site_code = serializers.SerializerMethodField()
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

    def get_accredited(self, obj):
        site_visit = SiteVisit.objects.get(id=obj['sass_id'])
        owner = site_visit.owner
        if not owner:
            return 'N'
        if owner.bims_profile.is_accredited():
            return 'Y'
        else:
            return 'N'

    def get_reference_category(self, obj):
        return obj['reference_category']

    def get_study_reference(self, obj):
        return obj['reference']

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
        return obj['full_name']

    def get_sass_version(self, obj):
        return obj['sass_version']

    def get_sass_score(self, obj):
        return obj['sass_score']

    def get_number_of_taxa(self, obj):
        return obj['count']

    def get_ASPT(self, obj):
        return '{0:.2f}'.format(obj['aspt'])

    def get_sampling_date(self, obj):
        site_visit_date = obj['sampling_date']
        return site_visit_date.strftime('%d-%m-%Y')

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
            'reference_category',
            'study_reference',
            'owner',
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
