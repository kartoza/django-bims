from bims.models import IUCNStatus
from bims.models.taxonomy import Taxonomy
from rest_framework.views import APIView, Response
from django.db.models import Case, F, Count, Value, When, CharField
from django.db.models.functions import ExtractYear, ExtractMonth, Concat, LPad, Cast
from bims.api_views.search import CollectionSearch

PER_YEAR_FREQUENCY = 'y'
PER_MONTH_FREQUENCY = 'm'


class ChartDataApiView(APIView):
    data_frequency = PER_YEAR_FREQUENCY

    def format_data(self, collection_data, categories):
        chart_data = {
            'dataset_labels': categories,
            'labels': [],
            'data': {category: [] for category in categories},
            'colours': self.colors()
        }

        if self.data_frequency == PER_MONTH_FREQUENCY:
            year_labels = sorted({data['year'] for data in collection_data},
                                 key=lambda x: (x.split('-')[1], x.split('-')[0]))
        else:
            year_labels = sorted({data['year'] for data in collection_data})

        data_counts = {
            year: {category: 0 for category in categories}
            for year in year_labels}
        for data in collection_data:
            data_counts[data['year']][data['name']] += data['count']
        for year in year_labels:
            for category in categories:
                chart_data['data'][category].append(
                    data_counts[year][category])

        chart_data['labels'] = year_labels

        return chart_data

    def chart_data_per_month(self, collection_results):
        raise NotImplementedError

    def chart_data(self, collection_results):
        raise NotImplementedError

    def categories(self, collection_results):
        raise NotImplementedError

    def colors(self):
        return {}

    def get(self, request):
        filters = request.GET.dict()

        self.data_frequency = filters.get('d', PER_YEAR_FREQUENCY)
        filters['requester'] = self.request.user.id

        search = CollectionSearch(filters)
        collection_results = search.process_search()
        if self.data_frequency == PER_YEAR_FREQUENCY:
            chart_data = self.chart_data(collection_results)
        else:
            chart_data = self.chart_data_per_month(collection_results)

        categories = self.categories(collection_results)
        result = self.format_data(
            chart_data,
            categories
        )
        return Response(result)


class OccurrencesChartData(ChartDataApiView):
    """
    Get occurrence data categorized by origin for chart
    """

    def categories(self, collection_results):
        return list(collection_results.annotate(
            name=Case(
                When(taxonomy__origin='', then=Value('Unknown')),
                When(taxonomy__origin__icontains='unknown',
                     then=Value('Unknown')),
                default=F('taxonomy__origin'))
        ).values_list(
            'name', flat=True
        ).distinct('name'))

    def chart_data_per_month(self, collection_results):
        return collection_results.annotate(
            y=ExtractYear('collection_date'),
            m=LPad(Cast(ExtractMonth('collection_date'), CharField()), 2, Value('0')),
            year=Concat(
                'm', Value('-'), 'y',
                output_field=CharField()
            ),
            name=Case(
                When(taxonomy__origin='', then=Value('Unknown')),
                When(taxonomy__origin__icontains='unknown',
                     then=Value('Unknown')),
                default=F('taxonomy__origin'))
        ).values(
            'year', 'name'
        ).annotate(
            count=Count('year'),
        ).values(
            'year', 'name', 'count'
        ).order_by('collection_date')

    def chart_data(self, collection_results):
        return collection_results.annotate(
            year=ExtractYear('collection_date'),
            name=Case(
                When(taxonomy__origin='', then=Value('Unknown')),
                When(taxonomy__origin__icontains='unknown',
                     then=Value('Unknown')),
                default=F('taxonomy__origin'))
        ).values(
            'year', 'name'
        ).annotate(
            count=Count('year'),
        ).values(
            'year', 'name', 'count'
        ).order_by('year')


class LocationSitesConservationChartData(ChartDataApiView):
    """
    Conservation status chart data from filtered collection records
    """

    def categories(self, collection_results):
        return list(collection_results.annotate(
            name=Case(When(taxonomy__iucn_status__category__isnull=False,
                           then=F('taxonomy__iucn_status__category')),
                      default=Value('NE'))
        ).values_list(
            'name', flat=True
        ).distinct('name'))

    def colors(self):
        return dict(IUCNStatus.objects.filter(
            national=False
        ).values_list(
            'category', 'colour')
        )

    def chart_data_per_month(self, collection_results):
        return collection_results.annotate(
            y=ExtractYear('collection_date'),
            m=LPad(Cast(ExtractMonth('collection_date'), CharField()), 2, Value('0')),
            year=Concat(
                'm', Value('-'), 'y',
                output_field=CharField()
            ),
            name=Case(When(taxonomy__iucn_status__category__isnull=False,
                           then=F('taxonomy__iucn_status__category')),
                      default=Value('NE')),
        ).values(
            'year', 'name'
        ).annotate(
            count=Count('year'),
        ).values(
            'year', 'name', 'count'
        ).order_by('collection_date')

    def chart_data(self, collection_results):
        return collection_results.annotate(
            year=ExtractYear('collection_date'),
            name=Case(When(taxonomy__iucn_status__category__isnull=False,
                           then=F('taxonomy__iucn_status__category')),
                      default=Value('NE')),
        ).values(
            'year', 'name'
        ).annotate(
            count=Count('year'),
        ).values(
            'year', 'name', 'count'
        ).order_by('year')


class LocationSitesTaxaChartData(ChartDataApiView):
    """
    """
    taxa = None

    def categories(self, collection_results):
        if not self.taxa:
            self.taxa = Taxonomy.objects.filter(
                biologicalcollectionrecord__id__in=
                collection_results.values_list('id', flat=True)
            ).distinct()[:25]
        return list(collection_results.filter(
            taxonomy__in=self.taxa
        ).annotate(
            name=F('taxonomy__scientific_name'),
        ).values_list(
            'name', flat=True
        ).distinct('name'))

    def chart_data_per_month(self, collection_results):
        if not self.taxa:
            self.taxa = Taxonomy.objects.filter(
                biologicalcollectionrecord__id__in=
                collection_results.values_list('id', flat=True)
            ).distinct()[:25]
        return collection_results.filter(
            taxonomy__in=self.taxa
        ).annotate(
            y=ExtractYear('collection_date'),
            m=LPad(Cast(ExtractMonth('collection_date'), CharField()), 2, Value('0')),
            year=Concat(
                'm', Value('-'), 'y',
                output_field=CharField()
            ),
            name=F('taxonomy__scientific_name'),
        ).values(
            'year', 'name'
        ).annotate(
            count=Count('year'),
        ).values(
            'year', 'name', 'count'
        ).order_by('collection_date')

    def chart_data(self, collection_results):
        if not self.taxa:
            self.taxa = Taxonomy.objects.filter(
                biologicalcollectionrecord__id__in=
                collection_results.values_list('id', flat=True)
            ).distinct()[:25]
        return collection_results.filter(
            taxonomy__in=self.taxa
        ).annotate(
            year=ExtractYear('collection_date'),
            name=F('taxonomy__scientific_name'),
        ).values(
            'year', 'name'
        ).annotate(
            count=Count('year'),
        ).values(
            'year', 'name', 'count'
        ).order_by('year')


class LocationSitesEndemismChartData(ChartDataApiView):
    """
    Return data for endemism bar chart.
    """

    def categories(self, collection_results):
        return list(collection_results.annotate(
            name=Case(When(taxonomy__endemism__isnull=False,
                           then=F('taxonomy__endemism__name')),
                      default=Value('Unknown'))
        ).values_list(
            'name', flat=True
        ).distinct('name'))

    def chart_data_per_month(self, collection_results):
        return collection_results.annotate(
            y=ExtractYear('collection_date'),
            m=LPad(Cast(ExtractMonth('collection_date'), CharField()), 2, Value('0')),
            year=Concat(
                'm', Value('-'), 'y',
                output_field=CharField()
            ),
            name=Case(When(taxonomy__endemism__isnull=False,
                           then=F('taxonomy__endemism__name')),
                      default=Value('Unknown'))
        ).values(
            'year', 'name'
        ).annotate(
            count=Count('year'),
        ).values(
            'year', 'name', 'count'
        ).order_by('collection_date')

    def chart_data(self, collection_results):
        return collection_results.annotate(
            year=ExtractYear('collection_date'),
            name=Case(When(taxonomy__endemism__isnull=False,
                           then=F('taxonomy__endemism__name')),
                      default=Value('Unknown'))
        ).values(
            'year', 'name'
        ).annotate(
            count=Count('year'),
        ).values(
            'year', 'name', 'count'
        ).order_by('year')
