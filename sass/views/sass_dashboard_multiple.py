from django.views.generic import TemplateView
from django.db.models import (
    Case, When, F, Count, Sum, FloatField,
)
from django.db.models.functions import Cast
from rest_framework.views import APIView
from rest_framework.response import Response
from bims.api_views.search_version_2 import SearchVersion2
from bims.models import LocationSite
from sass.models import SiteVisitTaxon


class SassDashboardMultipleSitesView(TemplateView):
    template_name = 'sass_dashboard_multiple_sites.html'


class SassDashboardMultipleSitesApiView(APIView):
    site_visit_taxa = SiteVisitTaxon.objects.none()

    def get_sass_score_chart_data(self):
        summary = self.site_visit_taxa.annotate(
            site_code=Case(
                When(site_visit__location_site__site_code__isnull=False,
                     then='site_visit__location_site__site_code'),
                default='site_visit__location_site__name'
            ),
        ).values('site_code').annotate(
            count=Count('sass_taxon'),
            sass_score=Case(
                When(site_visit__sass_version=5, then=Sum(
                    'sass_taxon__sass_5_score')),
                When(site_visit__sass_version=4, then=Sum(
                    'sass_taxon__score')),
                default=Sum('sass_taxon__sass_5_score')),
        ).annotate(
            aspt=Cast(F('sass_score'), FloatField()) / Cast(F('count'),
                                                            FloatField()),
        )
        chart_data = {
            'site_code': [],
            'sass_score': [],
            'aspt_score': [],
            'taxa_count': []
        }
        for data in summary:
            chart_data['site_code'].append(
                data['site_code']
            )
            chart_data['sass_score'].append(
                data['sass_score']
            )
            chart_data['aspt_score'].append(
                round(data['aspt'], 2)
            )
            chart_data['taxa_count'].append(
                data['count']
            )
        return chart_data

    def get(self, request):
        filters = request.GET
        site_ids = filters.get('siteId', '')
        search = SearchVersion2(filters)
        collection_records = search.process_search()
        self.site_visit_taxa = SiteVisitTaxon.objects.filter(
            id__in=collection_records
        )
        sass_score_chart_data = self.get_sass_score_chart_data()

        location_sites = LocationSite.objects.filter(
            id__in=site_ids.split(',')
        ).distinct()
        coordinates = []
        for location_site in location_sites:
            coordinates.append({
                'x': location_site.get_centroid().x,
                'y': location_site.get_centroid().y
            })
        return Response({
            'sass_score_chart_data': sass_score_chart_data,
            'coordinates': coordinates
        })
