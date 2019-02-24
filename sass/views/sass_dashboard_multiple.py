from collections import OrderedDict
from django.views.generic import TemplateView
from django.contrib.postgres.fields.jsonb import KeyTextTransform
from django.db.models import (
    Case, When, F, Count, Sum, FloatField, Avg, Min, Max, Q
)
from django.db.models.functions import Cast
from rest_framework.views import APIView
from rest_framework.response import Response
from bims.api_views.search_version_2 import SearchVersion2
from bims.models import LocationSite
from sass.models import (
    SiteVisitTaxon,
    SiteVisitBiotopeTaxon,
    SassEcologicalCategory,
    SassEcologicalCondition
)


class SassDashboardMultipleSitesView(TemplateView):
    template_name = 'sass_dashboard_multiple_sites.html'


class SassDashboardMultipleSitesApiView(APIView):
    site_visit_taxa = SiteVisitTaxon.objects.none()
    location_sites = LocationSite.objects.none()

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
            sass_score=Sum(Case(
                When(
                    condition=Q(site_visit__sass_version=5,
                                sass_taxon__sass_5_score__isnull=False),
                    then='sass_taxon__sass_5_score'),
                default='sass_taxon__score'
            )),
        ).annotate(
            aspt=Cast(F('sass_score'), FloatField()) / Cast(F('count'),
                                                            FloatField()),
        ).order_by('-date')
        chart_data = {
            'sass_ids': [],
            'site_id': [],
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
            chart_data['site_id'].append(
                data['site_id']
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

    def get_taxa_per_biotope_data(self):
        latest_site_visits = self.site_visit_taxa.order_by(
            'site',
            '-site_visit__site_visit_date'
        ).distinct('site').values('site_visit')
        sass_taxon_data = (
            self.site_visit_taxa.filter(
                site_visit__in=latest_site_visits
            ).annotate(
                site_code=Case(
                    When(site_visit__location_site__site_code__isnull=False,
                         then='site_visit__location_site__site_code'),
                    default='site_visit__location_site__name'
                ),
                taxon_name=Case(
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
                site_id=F('site_visit__location_site__id'),
                canonical_name=F('taxonomy__canonical_name'),
                abundance=F('taxon_abundance__abc'),
                score=F('sass_score'),
            ).values(
                'site_id',
                'site_code',
                'sass_taxon_id',
                'canonical_name',
                'abundance',
                'taxon_name',
                'score')
            .order_by('canonical_name', 'taxon_name')
        )
        biotope_data = (
            SiteVisitBiotopeTaxon.objects.filter(
                sass_taxon__in=self.site_visit_taxa.values_list('sass_taxon'),
                site_visit__in=latest_site_visits
            ).annotate(
                canonical_name=F('taxon__canonical_name'),
                abundance=F('taxon_abundance__abc'),
                biotope_name=F('biotope__name'),
                site_id=F('site_visit__location_site__id'),
            ).values(
                'site_id',
                'biotope_name',
                'sass_taxon_id',
                'canonical_name',
                'abundance')
        )
        sass_taxon_data_dict = OrderedDict()
        for taxon_data in list(sass_taxon_data):
            name = '{name}-{sass_taxon_id}'.format(
                name=taxon_data['canonical_name'],
                sass_taxon_id=taxon_data['sass_taxon_id']
            )
            site_id = taxon_data['site_id']
            if name not in sass_taxon_data_dict:
                sass_taxon_data_dict[name] = taxon_data
                sass_taxon_data_dict[name]['site_abundance'] = {}
            sass_taxon_data_dict[name]['site_abundance'][site_id] = (
                taxon_data['abundance']
            )
            try:
                sass_taxon_data_dict[name].pop('site_id')
                sass_taxon_data_dict[name].pop('abundance')
                sass_taxon_data_dict[name].pop('site_code')
            except KeyError:
                pass

        for biotope in biotope_data:
            key = '{name}-{sass_taxon_id}'.format(
                name=biotope['canonical_name'],
                sass_taxon_id=biotope['sass_taxon_id']
            )
            site_id = str(biotope['site_id'])
            if key in sass_taxon_data_dict:
                if 'biotope_data' not in sass_taxon_data_dict[key]:
                    sass_taxon_data_dict[key]['biotope_data'] = {}
                if site_id not in sass_taxon_data_dict[key]['biotope_data']:
                    sass_taxon_data_dict[key]['biotope_data'][site_id] = {}
                sass_taxon_data_dict[key][
                    'biotope_data'][site_id][biotope['biotope_name']] = (
                    biotope['abundance']
                )
        return sass_taxon_data_dict

    def get_biotope_ratings_chart_data(self, sass_ids=None):
        data = {}

        biotope_ratings = self.site_visit_taxa.filter(
            site_visit_id__in=sass_ids,
            site_visit__sass_biotope_fraction__sass_biotope__biotope_form=1
        ).annotate(
            site_code=Case(
                When(site_visit__location_site__site_code__isnull=False,
                     then='site_visit__location_site__site_code'),
                default='site_visit__location_site__name'
            ),
            date=F('site_visit__site_visit_date'),
            rate=F('site_visit__sass_biotope_fraction__rate__rate'),
            biotope=F('site_visit__sass_biotope_fraction__sass_biotope__name')
        ).values('date', 'rate', 'biotope', 'site_id', 'site_code').order_by(
            '-site_visit__site_visit_date',
            'site_visit__sass_biotope_fraction__sass_biotope__display_order'
        ).distinct()

        biotope_labels = []

        for rating_data in biotope_ratings:
            date = rating_data['date'].strftime('%d-%m-%Y')
            site_id = rating_data['site_id']
            if site_id not in data:
                data[site_id] = {}
            rate = rating_data['rate']
            biotope = rating_data['biotope'].encode('utf-8')
            if not rate:
                rate = 0
            data[site_id]['date'] = date
            data[site_id]['site_code'] = rating_data['site_code']
            data[site_id][biotope] = rate
            if biotope not in biotope_labels:
                biotope_labels.append(biotope)

        return {
            'rating_data': data,
            'biotope_labels': biotope_labels
        }

    def get_ecological_chart_data(self):
        chart_data = {}
        unique_ecoregions = []
        all_chart_data = []
        eco_geo_data = (self.location_sites.annotate(
            geo_class=KeyTextTransform(
                'value', KeyTextTransform(
                    'geo_class',
                    KeyTextTransform(
                        'service_registry_values',
                        KeyTextTransform(
                            'eco_geo_group',
                            KeyTextTransform(
                                'context_group_values',
                                'location_context'))))),
            eco_region=KeyTextTransform(
                'value', KeyTextTransform(
                    'eco_region',
                    KeyTextTransform(
                        'service_registry_values',
                        KeyTextTransform(
                            'eco_geo_group',
                            KeyTextTransform(
                                'context_group_values',
                                'location_context')))))
        ).values('geo_class', 'eco_region', 'id')).distinct()

        unique_eco_geo = {}
        max_charts = 4
        for eco_geo in eco_geo_data:
            eco_region = eco_geo['eco_region']
            geo_class = eco_geo['geo_class']
            if not eco_region or not geo_class:
                continue
            tuple_key = (eco_region, geo_class)
            if tuple_key not in unique_eco_geo:
                unique_eco_geo[tuple_key] = []
            unique_eco_geo[tuple_key].append(eco_geo['id'])

        index = 0
        for eco_geo, site_ids in unique_eco_geo.iteritems():
            if index >= max_charts:
                unique_ecoregions.append({
                    'eco_regions': eco_geo,
                    'site_ids': site_ids
                })
                continue
            index += 1
            eco_region = eco_geo[0]
            geo_class = eco_geo[1]
            ecological_conditions = SassEcologicalCondition.objects.filter(
                ecoregion_level_1__icontains=eco_region,
                geomorphological_zone__icontains=geo_class
            )

            if not ecological_conditions:
                # check Combined data
                geo_class = 'combined'
                ecological_conditions = (
                    SassEcologicalCondition.objects.filter(
                        ecoregion_level_1__icontains=eco_region,
                        geomorphological_zone__icontains=geo_class
                    ))

            ecological_conditions = ecological_conditions.annotate(
                ec_name=F('ecological_category__name'),
                ec_category=F(
                    'ecological_category__category'),
                color=F('ecological_category__colour'),
                sass=F('sass_score_precentile'),
                aspt=F('aspt_score_precentile'),
            ).values(
                'ec_name',
                'ec_category',
                'color',
                'sass',
                'aspt'
            ).order_by('ecological_category__order')
            chart_data = list(ecological_conditions)
            if chart_data:
                lowest_category = SassEcologicalCategory.objects.filter(
                    Q(category__icontains='e') |
                    Q(category__icontains='f')
                )
                if lowest_category.exists():
                    lowest_category = lowest_category[0]
                    chart_data.append({
                        'ec_name': lowest_category.name,
                        'ec_category': 'E/F',
                        'color': lowest_category.colour,
                        'sass': 0,
                        'aspt': 0.0
                    })
            all_chart_data.append({
                'chart_data': chart_data,
                'site_data': {
                    'site_ids': site_ids,
                    'eco_region': eco_region,
                    'geo_class': geo_class
                }
            })
        return all_chart_data, unique_ecoregions

    def get(self, request):
        filters = request.GET
        search = SearchVersion2(filters)
        collection_records = search.process_search()
        self.site_visit_taxa = SiteVisitTaxon.objects.filter(
            id__in=collection_records
        )
        sass_score_chart_data = self.get_sass_score_chart_data()
        taxa_per_biotope_data = self.get_taxa_per_biotope_data()
        biotope_ratings_chart_data = self.get_biotope_ratings_chart_data(
            sass_ids=sass_score_chart_data['sass_ids']
        )

        self.location_sites = LocationSite.objects.filter(
            id__in=collection_records.values('site').distinct()
        )
        coordinates = []
        ecological_chart_data, unique_ecoregions = (
            self.get_ecological_chart_data()
        )
        for location_site in self.location_sites:
            coordinates.append({
                'x': location_site.get_centroid().x,
                'y': location_site.get_centroid().y
            })
        return Response({
            'sass_score_chart_data': sass_score_chart_data,
            'taxa_per_biotope_data': taxa_per_biotope_data,
            'biotope_ratings_chart_data': biotope_ratings_chart_data,
            'ecological_chart_data': ecological_chart_data,
            'unique_ecoregions': unique_ecoregions,
            'coordinates': coordinates,
            'data_sources': list(
                self.site_visit_taxa.exclude(
                    site_visit__data_source__isnull=True
                ).values_list(
                    'site_visit__data_source__name',
                    flat=True
                ).distinct())
        })
