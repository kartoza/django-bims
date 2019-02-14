from rest_framework import serializers
from django.db.models import Q
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
