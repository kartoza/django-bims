import json
from django.views.generic import TemplateView
from django.shortcuts import get_object_or_404
from django.http import Http404
from django.db.models import (
    Case, When, F, Count, Sum, FloatField,
    IntegerField, Q
)
from django.db.models.functions import Cast, Coalesce
from bims.models.location_site import LocationSite
from bims.api_views.search_version_2 import SearchVersion2
from sass.models import (
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
            date=F('site_visit__site_visit_date'),
        ).values('date').annotate(
            count=Count('sass_taxon'),
            sass_score=Sum(Case(
                When(
                    condition=Q(site_visit__sass_version=5,
                                sass_taxon__sass_5_score__isnull=False),
                    then='sass_taxon__sass_5_score'),
                default='sass_taxon__score'
            )),
            sass_id=F('site_visit__id')
        ).annotate(
            aspt=Cast(F('sass_score'), FloatField()) / Cast(F('count'),
                                                            FloatField()),
        ).order_by('date')

        data['date_labels'] = (
            [dt.strftime('%d-%m-%Y')
             for dt in summary.values_list('date', flat=True)])
        data['taxa_numbers'] = list(
            summary.values_list('count', flat=True))
        data['sass_scores'] = list(
            summary.values_list('sass_score', flat=True))
        data['aspt_list'] = list(
            summary.values_list('aspt', flat=True))
        data['sass_ids'] = list(
            summary.values_list('sass_id', flat=True))
        return data

    def get_sass_taxon_table_data(self):
        data = {}
        latest_site_visit = (
            self.site_visit_taxa.
            order_by('-site_visit__site_visit_date')[0].site_visit
        )
        sass_taxon_data = (
            self.site_visit_taxa.filter(
                site_visit=latest_site_visit
            ).annotate(
                sass_taxon_name=Case(
                    When(
                        condition=Q(site_visit__sass_version=5,
                                    sass_taxon__taxon_sass_5__isnull=False),
                        then='sass_taxon__taxon_sass_5'),
                    default='sass_taxon__taxon_sass_4'
                ),
                sass_score=Case(
                    When(
                        condition=Q(site_visit__sass_version=5,
                                    sass_taxon__sass_5_score__isnull=False),
                        then='sass_taxon__sass_5_score'),
                    default='sass_taxon__score'
                ),
            ).values(
                'sass_taxon_id',
                'taxonomy__canonical_name',
                'taxon_abundance__abc',
                'sass_taxon_name',
                'sass_score')
            .order_by('taxonomy__canonical_name', 'sass_taxon_name')
        )

        biotope_data = (
            SiteVisitBiotopeTaxon.objects.filter(
                sass_taxon__in=self.site_visit_taxa.values_list('sass_taxon'),
                site_visit=latest_site_visit).values(
                'biotope__name', 'sass_taxon', 'taxon_abundance__abc')
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
                highly_tolerant=Coalesce(Sum('highly_tolerant_value'), 0),
                tolerant=Coalesce(Sum('tolerant_value'), 0),
                sensitive=Coalesce(Sum('sensitive_value'), 0),
                highly_sensitive=Coalesce(Sum('highly_sensitive_value'), 0)
            )
        )

        return sensitivity_data

    def get_biotope_ratings_chart_data(self):
        data = {}

        biotope_ratings = self.site_visit_taxa.filter(
            site_visit__sass_biotope_fraction__sass_biotope__biotope_form=1
        ).annotate(
            date=F('site_visit__site_visit_date'),
            rate=F('site_visit__sass_biotope_fraction__rate__rate'),
            biotope=F('site_visit__sass_biotope_fraction__sass_biotope__name')
        ).values('date', 'rate', 'biotope').order_by(
            'site_visit__site_visit_date',
            'site_visit__sass_biotope_fraction__sass_biotope__display_order'
        ).distinct()

        biotope_labels = []

        for rating_data in biotope_ratings:
            date = rating_data['date'].strftime('%d-%m-%Y')
            if date not in data:
                data[date] = {}
            rate = rating_data['rate']
            biotope = rating_data['biotope'].encode('utf-8')
            if not rate:
                rate = 0
            data[date][biotope] = rate
            if biotope not in biotope_labels:
                biotope_labels.append(biotope)

        return {
            'rating_data': data,
            'biotope_labels': biotope_labels
        }

    def get_context_data(self, **kwargs):
        context = super(SassDashboardView, self).get_context_data(**kwargs)
        self.get_site_visit_taxon()
        context['coord'] = [
            self.location_site.get_centroid().x,
            self.location_site.get_centroid().y
        ]
        context['site_code'] = self.location_site.site_code
        context['site_id'] = self.location_site.id
        context['site_description'] = self.location_site.site_description

        if not self.site_visit_taxa:
            context['sass_exists'] = False
            return context

        context['sass_exists'] = True

        context['sass_score_chart_data'] = self.get_sass_score_chart_data()
        context['sass_taxon_table_data'] = self.get_sass_taxon_table_data()
        context['sensitivity_chart_data'] = self.get_sensitivity_chart_data()
        context['biotope_ratings_chart_data'] = (
            self.get_biotope_ratings_chart_data()
        )
        context['data_sources'] = list(
            self.site_visit_taxa.exclude(
                site_visit__data_source__isnull=True
            ).values_list(
                'site_visit__data_source__name',
                flat=True
            ).distinct())

        try:
            location_context = json.loads(self.location_site.location_context)
            context['river_catchments'] = (
                json.dumps(
                    location_context['context_group_values'][
                        'water_group']['service_registry_values']
                )
            )
        except (KeyError, TypeError):
            pass

        return context

    def get(self, request, *args, **kwargs):
        site_id = kwargs.get('site_id', None)
        if not site_id or not request.GET or not request.GET.get(
            'siteId', None):
            raise Http404()
        self.location_site = get_object_or_404(
            LocationSite,
            pk=site_id
        )
        return super(SassDashboardView, self).get(request, *args, **kwargs)
