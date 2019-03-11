from rest_framework import serializers
import json
from django.db.models import Q
from bims.models import LocationSite
from sass.models import SiteVisitTaxon, SiteVisitBiotopeTaxon


class SassDataSerializer(serializers.ModelSerializer):

    date = serializers.SerializerMethodField()
    sass_version = serializers.SerializerMethodField()
    taxa = serializers.SerializerMethodField()
    sass_taxa = serializers.SerializerMethodField()
    weight = serializers.SerializerMethodField()
    s = serializers.SerializerMethodField()
    v = serializers.SerializerMethodField()
    g = serializers.SerializerMethodField()
    site = serializers.SerializerMethodField()
    site_code = serializers.SerializerMethodField()

    def get_site_code(self, obj):
        site_code = obj.site_visit.location_site.site_code
        if not site_code:
            return obj.site_visit.location_site.name
        return site_code

    def get_date(self, obj):
        return obj.site_visit.site_visit_date

    def get_sass_version(self, obj):
        return obj.site_visit.sass_version

    def get_taxa(self, obj):
        return obj.taxonomy.canonical_name

    def get_sass_taxa(self, obj):
        if obj.site_visit.sass_version == 4:
            return obj.sass_taxon.taxon_sass_4
        else:
            return obj.sass_taxon.taxon_sass_5

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

    class Meta:
        model = SiteVisitTaxon
        fields = [
            'site_code',
            'date',
            'sass_version',
            'taxa',
            'sass_taxa',
            'weight',
            's',
            'v',
            'g',
            'site'
        ]


class SassSummaryDataSerializer(serializers.ModelSerializer):

    site_code = serializers.SerializerMethodField()
    sass_score = serializers.SerializerMethodField()
    taxa_number = serializers.SerializerMethodField()
    aspt = serializers.SerializerMethodField()
    date = serializers.SerializerMethodField()
    assessor = serializers.SerializerMethodField()
    sass_version = serializers.SerializerMethodField()

    def get_site_code(self, obj):
        return obj['site_code']

    def get_assessor(self, obj):
        return obj['assessor']

    def get_sass_version(self, obj):
        return obj['sass_version']

    def get_sass_score(self, obj):
        return obj['sass_score']

    def get_taxa_number(self, obj):
        return obj['count']

    def get_aspt(self, obj):
        return '{0:.2f}'.format(obj['aspt'])

    def get_date(self, obj):
        site_visit_date = obj['date']
        return site_visit_date.strftime('%d-%m-%Y')

    def group_fields(self, context_key, site_id, result):
        try:
            location_site = LocationSite.objects.get(
                id=site_id
            )
        except LocationSite.DoesNotExist:
            return ''
        location_context = json.loads(
            location_site.location_context
        )
        try:
            context_group = (
                location_context['context_group_values'][context_key]
            )
            for registry_value in context_group['service_registry_values']:
                registry_data = (
                    context_group['service_registry_values'][registry_value]
                )
                if registry_data['value']:
                    key_name = \
                        '{} ({})'.format(registry_data['name'], context_key)
                    result[key_name] = registry_data['value']
            return result
        except KeyError:
            return ''

    class Meta:
        model = SiteVisitTaxon
        fields = [
            'date',
            'site_code',
            'sass_score',
            'taxa_number',
            'aspt',
            'assessor',
            'sass_version',
        ]

    def to_representation(self, obj):
        result = super(SassSummaryDataSerializer, self).to_representation(obj)
        site_id = obj['site_id']
        result = self.group_fields('water_group', site_id, result)
        result = self.group_fields('eco_geo_group', site_id, result)
        return result
