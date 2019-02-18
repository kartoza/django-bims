from django.views.generic import TemplateView
from django.db.models import (
    Case, When, F, Count, Sum, FloatField, Avg, Min, Max
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
            date=F('site_visit__site_visit_date'),
            site_code=Case(
                When(site_visit__location_site__site_code__isnull=False,
                     then='site_visit__location_site__site_code'),
                default='site_visit__location_site__name'
            ),
            sass_id=F('site_visit__id'),
            site_id=F('site_visit__location_site__id'),
        ).values('site_code', 'date', 'site_id', 'sass_id').annotate(
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
        ).order_by('-date')
        chart_data = {
            'sass_ids': [],
            'site_code': [],
            'sass_score': [],
            'aspt_score': [],
            'taxa_count': [],
            'date': [],
            'aspt_average': [],
            'taxa_number_average': [],
            'sass_score_average': [],
            'number_assessments': [],
        }
        site_codes = []
        for data in summary:
            # Get the latest data
            if data['site_code'] in site_codes:
                continue
            site_codes.append(data['site_code'])

            chart_data['site_code'].append(
                data['site_code']
            )
            chart_data['sass_ids'].append(
                data['sass_id']
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
            chart_data['date'].append(
                data['date'].strftime('%d-%m-%Y')
            )
            chart_data['number_assessments'].append(
                len(summary.filter(site=data['site_id']))
            )
            averages = summary.filter(site=data['site_id']).aggregate(
                taxa_number_average=Avg('count'),
                sass_score_average=Avg('sass_score'),
                aspt_average=Avg('aspt'),
                taxa_number_min=Min('count'),
                sass_score_min=Min('sass_score'),
                aspt_min=Min('aspt'),
                taxa_number_max=Max('count'),
                sass_score_max=Max('sass_score'),
                aspt_max=Max('aspt')
            )
            chart_data['taxa_number_average'].append({
                'avg': averages['taxa_number_average'],
                'min': averages['taxa_number_min'],
                'max': averages['taxa_number_max'],
            })
            chart_data['sass_score_average'].append({
                'avg': averages['sass_score_average'],
                'min': averages['sass_score_min'],
                'max': averages['sass_score_max'],
            })
            chart_data['aspt_average'].append({
                'avg': averages['aspt_average'],
                'min': averages['aspt_min'],
                'max': averages['aspt_max'],
            })
        return chart_data

    def get(self, request):
        filters = request.GET
        search = SearchVersion2(filters)
        collection_records = search.process_search()
        self.site_visit_taxa = SiteVisitTaxon.objects.filter(
            id__in=collection_records
        )
        sass_score_chart_data = self.get_sass_score_chart_data()

        location_sites = LocationSite.objects.filter(
            id__in=collection_records.values('site').distinct()
        )
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
