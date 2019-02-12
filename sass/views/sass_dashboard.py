import json
from django.views.generic import TemplateView
from django.shortcuts import get_object_or_404
from django.http import Http404
from django.db.models import (
    Case, When, F, Count, Sum, FloatField, Value,
    IntegerField, Q
)
from django.db.models.functions import ExtractYear, Cast
from bims.models.location_site import LocationSite
from bims.api_views.search_version_2 import SearchVersion2
from sass.models import (
    SiteVisit,
    SiteVisitTaxon,
    SiteVisitBiotopeTaxon
)


class SassDashboardView(TemplateView):
    template_name = 'sass_dashboard_single_site.html'
    location_site = LocationSite.objects.none()
    site_visit_taxa = SiteVisitTaxon.objects.none()

    def get_site_visit_taxon(self):
        filters = self.request.GET
        search = SearchVersion2(filters)
        collection_records = search.process_search()
        self.site_visit_taxa = SiteVisitTaxon.objects.filter(
            id__in=collection_records
        )

    def get_sass_score_chart_data(self):
        data = {}
        summary = self.site_visit_taxa.annotate(
            year=ExtractYear('site_visit__site_visit_date')
        ).values('year').annotate(
            count=Count('sass_taxon'),
            sass_score=Case(
                When(site_visit__sass_version=5, then=Sum(
                    'sass_taxon__sass_5_score')),
                When(site_visit__sass_version=4, then=Sum(
                    'sass_taxon__score')),
                default=Sum('sass_taxon__sass_5_score')),
        ).annotate(
            aspt=Cast(F('sass_score'), FloatField()) /
                 Cast(F('count'), FloatField()),
        ).order_by('year')

        data['year_labels'] = list(
            summary.values_list('year', flat=True))
        data['taxa_numbers'] = list(
            summary.values_list('count', flat=True))
        data['sass_scores'] = list(
            summary.values_list('sass_score', flat=True))
        data['aspt_list'] = list(
            summary.values_list('aspt', flat=True))
        return data

    def get_sass_taxon_table_data(self):
        data = {}
        latest_site_visit = (
            self.site_visit_taxa.order_by('-site_visit__site_visit_date')[0].
                site_visit
        )
        sass_taxon_data = (
            self.site_visit_taxa.filter(
                site_visit=latest_site_visit
            ).annotate(
                sass_taxon_name=Case(
                    When(site_visit__sass_version=5, then=
                    'sass_taxon__taxon_sass_5'),
                    When(site_visit__sass_version=4, then=
                    'sass_taxon__taxon_sass_4'),
                    default='sass_taxon__taxon_sass_4'
                ),
                sass_score=Case(
                    When(site_visit__sass_version=5, then=
                    'sass_taxon__sass_5_score'),
                    When(site_visit__sass_version=4, then=
                    'sass_taxon__score'),
                    default='sass_taxon__sass_5_score'
                ),
            ).values(
                'taxonomy__canonical_name',
                'taxon_abundance__abc',
                'sass_taxon_name',
                'sass_score',
                'sass_taxon_id')
                .order_by('sass_taxon_name')
                .distinct('sass_taxon_name')
        )

        biotope_data = (
            SiteVisitBiotopeTaxon.objects.filter(
                sass_taxon__in=self.site_visit_taxa.values_list('sass_taxon'),
                site_visit=latest_site_visit).values(
                'biotope__name', 'sass_taxon','taxon_abundance__abc')
        )
        data['sass_taxon_data'] = json.dumps(list(sass_taxon_data))
        data['biotope_data'] = json.dumps(list(biotope_data))
        data['site_visit_date'] = latest_site_visit.site_visit_date
        return data

    def get_sensitivity_chart_data(self):
        # Ordered by
        # Highly tolerant = 1 - 3
        # Tolerant = 4 - 7
        # Sensitive = 8 - 11
        # Highly Sensitive 12 - 15
        sensitivity_data = (
            self.site_visit_taxa.annotate(
                sass_score=Case(
                    When(site_visit__sass_version=5,
                         then='sass_taxon__sass_5_score'),
                    When(site_visit__sass_version=4,
                         then='sass_taxon__score'),
                    default='sass_taxon__sass_5_score',
                    output_field=IntegerField()
                ),
            ).annotate(
                highly_tolerant_value=Case(
                    When(
                        condition=Q(
                            sass_score__gte=1, sass_score__lte=3),
                        then=1),
                    output_field=IntegerField()
                ),
                tolerant_value=Case(
                    When(
                        condition=Q(
                            sass_score__gte=4, sass_score__lte=7),
                        then=1),
                    output_field=IntegerField()
                ),
                sensitive_value=Case(
                    When(
                        condition=Q(
                            sass_score__gte=8, sass_score__lte=11),
                        then=1),
                    output_field=IntegerField()
                ),
                highly_sensitive_value=Case(
                    When(
                        condition=Q(
                            sass_score__gte=12, sass_score__lte=15),
                        then=1),
                    output_field=IntegerField()
                ),
            ).aggregate(
                highly_tolerant=Sum('highly_tolerant_value'),
                tolerant=Sum('tolerant_value'),
                sensitive=Sum('sensitive_value'),
                highly_sensitive=Sum('highly_sensitive_value')
            )
        )

        return sensitivity_data

    def get_context_data(self, **kwargs):
        context = super(SassDashboardView, self).get_context_data(**kwargs)
        context['coord'] = [
            self.location_site.get_centroid().x,
            self.location_site.get_centroid().y
        ]
        context['site_code'] = self.location_site.site_code
        context['site_description'] = self.location_site.site_description
        self.get_site_visit_taxon()

        context['sass_score_chart_data'] = self.get_sass_score_chart_data()
        context['sass_taxon_table_data'] = self.get_sass_taxon_table_data()
        context['sentivity_chart_data'] = self.get_sensitivity_chart_data()

        return context

    def get(self, request, *args, **kwargs):
        site_id = kwargs.get('site_id', None)
        if not site_id:
            return Http404()
        self.location_site = get_object_or_404(
            LocationSite,
            pk=site_id
        )
        return super(SassDashboardView, self).get(request, *args, **kwargs)
