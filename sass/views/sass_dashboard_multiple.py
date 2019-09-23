import time
from collections import OrderedDict
from django.views.generic import TemplateView
from django.contrib.postgres.fields.jsonb import KeyTextTransform
from django.db.models import (
    Case, When, F, Count, Sum, FloatField, Avg, Min, Max, Q
)
from django.db.models.functions import Cast
from django.core.paginator import Paginator
from rest_framework.views import APIView
from rest_framework.response import Response
from bims.api_views.search import Search
from bims.models import LocationSite
from bims.utils.logger import log
from sass.models import (
    SiteVisit,
    SiteVisitTaxon,
    SiteVisitBiotopeTaxon,
    SassEcologicalCategory,
    SassEcologicalCondition
)
from bims.enums.taxonomic_group_category import TaxonomicGroupCategory


def timing(f):
    def wrap(*args, **kwargs):
        time1 = time.time()
        ret = f(*args, **kwargs)
        time2 = time.time()
        log('%s function took %0.3f ms' % (
            f.func_name, (time2 - time1) * 1000.0))
        return ret
    return wrap


MAX_RESULTS_PER_PAGE = 50


class SassDashboardMultipleSitesView(TemplateView):
    template_name = 'sass_dashboard_multiple_sites.html'


class SassDashboardMultipleSitesApiView(APIView):
    site_visit_taxa = SiteVisitTaxon.objects.none()
    location_sites = LocationSite.objects.none()

    @timing
    def get_sass_score_chart_data(self):
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
        for data in self.location_sites:

            # Get the latest data
            site_visit = SiteVisit.objects.filter(
                location_site=data,
            ).order_by('-site_visit_date')
            if not site_visit:
                continue

            # Average
            averages = SiteVisitTaxon.objects.filter(
                site_visit__in=site_visit
            ).annotate(
                sass_id=F('site_visit__id'),
            ).values('sass_id').annotate(
                count=Count('sass_taxon'),
                sass_score=Sum(Case(
                    When(
                        condition=Q(site_visit__sass_version=5,
                                    sass_taxon__sass_5_score__isnull=False),
                        then='sass_taxon__sass_5_score'),
                    default='sass_taxon__score'
                ))
            ).annotate(
                aspt=Cast(
                    F('sass_score'), FloatField()) / Cast(
                    F('count'), FloatField()),
            ).aggregate(
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

            site_visit_index = 0
            latest_site_visit = site_visit[site_visit_index]
            if data.site_code in site_codes:
                continue
            sass_score_isnull = True
            site_visit_taxon = None
            site_visit_data = None
            while sass_score_isnull:
                site_visit_taxon = SiteVisitTaxon.objects.filter(
                    site_visit=latest_site_visit
                )
                site_visit_data = site_visit_taxon.aggregate(
                    sass_score=Sum(Case(
                        When(
                            condition=Q(
                                site_visit__sass_version=5,
                                sass_taxon__sass_5_score__isnull=False),
                            then='sass_taxon__sass_5_score'),
                        default='sass_taxon__score'
                    ))
                )
                if site_visit_data['sass_score']:
                    sass_score_isnull = False
                else:
                    site_visit_index += 1
                    if site_visit_index >= site_visit.count():
                        sass_score_isnull = False
                    latest_site_visit = site_visit[site_visit_index]

            if not site_visit_data or not site_visit_taxon:
                continue

            site_codes.append(data.site_code)
            chart_data['site_code'].append(data.site_code)
            chart_data['sass_ids'].append(latest_site_visit.id)
            chart_data['site_id'].append(data.id)
            sass_score = 0
            taxa_count = site_visit_taxon.distinct('sass_taxon').count()
            aspt = 0.0
            if site_visit_data:
                sass_score = site_visit_data['sass_score']
                try:
                    aspt = round(sass_score / taxa_count, 2)
                except TypeError:
                    pass
            chart_data['taxa_count'].append(taxa_count)
            chart_data['sass_score'].append(sass_score)
            chart_data['aspt_score'].append(aspt)
            chart_data['date'].append(
                latest_site_visit.site_visit_date.strftime('%d-%m-%Y')
            )
            chart_data['number_assessments'].append(
                site_visit.count()
            )
        return chart_data

    @timing
    def get_taxa_per_biotope_data(self):
        latest_site_visits = self.site_visit_taxa.order_by(
            'site',
            '-site_visit__site_visit_date'
        ).distinct('site').values('site_visit')
        sass_taxon_data = (
            self.site_visit_taxa.filter(
                site_visit__in=latest_site_visits,
                taxonomy__taxongroup__category=(
                    TaxonomicGroupCategory.SASS_TAXON_GROUP.name
                )
            ).annotate(
                site_code=Case(
                    When(site_visit__location_site__site_code__isnull=False,
                         then='site_visit__location_site__site_code'),
                    default='site_visit__location_site__name'
                ),
                taxon_name=F('sass_taxon__taxon_sass_4'),
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
                group_name=F('taxonomy__taxongroup__name'),
                display_order=Case(
                    When(
                        condition=Q(
                            site_visit__sass_version=5,
                            sass_taxon__display_order_sass_5__isnull=False),
                        then='sass_taxon__display_order_sass_5'),
                    default='sass_taxon__display_order_sass_4'
                ),
            ).values(
                'site_id',
                'site_code',
                'sass_taxon_id',
                'canonical_name',
                'abundance',
                'taxon_name',
                'score',
                'group_name',
                'display_order'
            )
            .order_by('display_order')
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

    @timing
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
            biotope_name=F(
                'site_visit__sass_biotope_fraction__sass_biotope__name')
        ).values(
            'date', 'rate', 'biotope_name', 'site_id', 'site_code').order_by(
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
            biotope = rating_data['biotope_name'].encode('utf-8')
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

    @timing
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
                            'geomorphological_group',
                            KeyTextTransform(
                                'context_group_values',
                                'location_context'))))),
            eco_region=KeyTextTransform(
                'value', KeyTextTransform(
                    'eco_region_1',
                    KeyTextTransform(
                        'service_registry_values',
                        KeyTextTransform(
                            'river_ecoregion_group',
                            KeyTextTransform(
                                'context_group_values',
                                'location_context')))))
        ).values('geo_class', 'eco_region', 'id'))

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

            # Fix eco_region name
            eco_region_splits = eco_region.split(' ')
            if eco_region_splits[0].isdigit():
                eco_region_splits.pop(0)
                eco_region = ' '.join(eco_region_splits)

            ecological_conditions = SassEcologicalCondition.objects.filter(
                ecoregion_level_1__icontains=eco_region,
                geomorphological_zone__icontains=geo_class
            )

            use_combined_geo = False
            if not ecological_conditions:
                use_combined_geo = True
            if (
                    not use_combined_geo and
                    not ecological_conditions.filter(
                        sass_score_precentile__isnull=False,
                        aspt_score_precentile__isnull=False).exists()
            ):
                use_combined_geo = True

            if use_combined_geo:
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
        filters = request.GET.dict()
        filters['validated'] = ''
        search = Search(filters)
        page = int(filters.get('page', 1))
        collection_records = search.process_search()
        collection_records_ids = collection_records.values_list(
            'id', flat=True
        )
        collection_records_site_ids = collection_records.distinct(
            'site'
        ).values_list(
            'site__id', flat=True
        )
        self.location_sites = LocationSite.objects.filter(
            id__in=list(collection_records_site_ids)
        ).order_by('site_code')

        paginator = Paginator(self.location_sites, MAX_RESULTS_PER_PAGE)
        if page > paginator.num_pages:
            page = paginator.count
        current_page = paginator.page(page)
        self.location_sites = current_page.object_list

        self.site_visit_taxa = SiteVisitTaxon.objects.filter(
            id__in=list(collection_records_ids),
            site__in=list(self.location_sites.values_list('id', flat=True))
        )
        sass_score_chart_data = self.get_sass_score_chart_data()
        taxa_per_biotope_data = self.get_taxa_per_biotope_data()
        biotope_ratings_chart_data = self.get_biotope_ratings_chart_data(
            sass_ids=sass_score_chart_data['sass_ids']
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

        collection_with_references = self.site_visit_taxa.exclude(
            source_reference__isnull=True
        ).distinct('source_reference')

        source_references = collection_with_references.source_references()

        return Response({
            'total_pages': paginator.num_pages,
            'current_page': page,
            'sass_score_chart_data': sass_score_chart_data,
            'taxa_per_biotope_data': taxa_per_biotope_data,
            'biotope_ratings_chart_data': biotope_ratings_chart_data,
            'ecological_chart_data': ecological_chart_data,
            'unique_ecoregions': unique_ecoregions,
            'coordinates': coordinates,
            'source_references': source_references
        })
