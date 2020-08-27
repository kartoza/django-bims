from rest_framework.views import APIView, Response
from django.db.models import Case, F, Count, Value, When
from django.db.models.functions import ExtractYear
from bims.api_views.search import CollectionSearch


class ChartDataApiView(APIView):

    def format_data(self, collection_data, categories):
        chart_data = {
            'dataset_labels': [],
            'labels': [],
            'data': {}
        }
        year_labels = []
        category_with_data = dict()
        for category in categories:
            category_with_data[category] = []

        for data in collection_data:
            new_data = False
            if data['year'] not in year_labels:
                new_data = True
                year_labels.append(data['year'])

            if new_data and len(year_labels) > 1:
                # Add 0 to previous
                for category in categories:
                    if len(category_with_data[category]) < len(
                            year_labels) - 1:
                        category_with_data[category].insert(
                            len(year_labels) - 2, 0)

            category_with_data[data['name']].append(data['count'])

        chart_data['dataset_labels'] = categories
        chart_data['labels'] = year_labels
        chart_data['data'] = category_with_data

        return chart_data

    def chart_data(self, collection_results):
        raise NotImplementedError

    def categories(self, collection_results):
        raise NotImplementedError

    def get(self, request):
        filters = request.GET.dict()
        search = CollectionSearch(filters)
        collection_results = search.process_search()
        chart_data = self.chart_data(collection_results)
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
            name=Case(When(category='',
                           then=Value('Unknown')),
                      default=F('category'))
        ).values_list(
            'name', flat=True
        ).distinct('name'))

    def chart_data(self, collection_results):
        return collection_results.annotate(
            year=ExtractYear('collection_date'),
            name=Case(When(category='',
                           then=Value('Unknown')),
                      default=F('category'))
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
                      default=Value('Not evaluated'))
        ).values_list(
            'name', flat=True
        ).distinct('name'))

    def chart_data(self, collection_results):
        return collection_results.annotate(
            year=ExtractYear('collection_date'),
            name=Case(When(taxonomy__iucn_status__category__isnull=False,
                           then=F('taxonomy__iucn_status__category')),
                      default=Value('Not evaluated')),
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
    def categories(self, collection_results):
        taxa = collection_results.values('taxonomy').distinct('taxonomy')[0:25]
        return list(collection_results.filter(
            taxonomy__in=taxa
        ).annotate(
            name=F('taxonomy__scientific_name'),
        ).values_list(
            'name', flat=True
        ).distinct('name'))

    def chart_data(self, collection_results):
        taxa = collection_results.values('taxonomy').distinct('taxonomy')[0:25]
        return collection_results.filter(
            taxonomy__in=taxa
        ).annotate(
            year=ExtractYear('collection_date'),
            name=F('taxonomy__scientific_name'),
        ).annotate(
            count=Count('year')
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
