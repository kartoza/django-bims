import matplotlib
matplotlib.use('Agg')  # noqa
import io
from collections import OrderedDict
from rest_framework.views import APIView, Response
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.figure import Figure
from django.http import HttpResponse, Http404
from django.db.models import Case, F, Count, Value, When
from django.db.models.functions import ExtractYear
from bims.api_views.search_version_2 import SearchVersion2 as Search


class LocationSitesEndemismChartData(APIView):
    """
    Return data for endemism bar chart.
    """

    def get(self, request):
        """
        Returns bar chart image
        """
        filters = request.GET.dict()
        search = Search(filters)
        collection_results = search.process_search()

        width = float(filters.get('width', 500))
        height = float(filters.get('height', 500))
        base_64 = bool(filters.get('base_64', 0))

        endemism_graph_data = collection_results.annotate(
            year=ExtractYear('collection_date'),
            name=Case(When(taxonomy__endemism__isnull=False,
                           then=F('taxonomy__endemism__name')),
                      default=Value('Unspecified'))
        ).values(
            'year', 'name'
        ).annotate(
            count=Count('year')
        ).values(
            'year', 'name', 'count'
        )

        endemism_labels = collection_results.annotate(
            name=Case(When(taxonomy__endemism__isnull=False,
                           then=F('taxonomy__endemism__name')),
                      default=Value('Unspecified'))
        ).values_list(
            'name', flat=True
        ).distinct(
            'name'
        )

        response_data = dict()

        for endemism in endemism_labels:
            response_data[endemism] = OrderedDict(
                endemism_graph_data.filter(
                    name=endemism
                ).values_list(
                    'year', 'count'
                ))
        if not response_data:
            raise Http404('No data')

        # Convert pixel to inches
        dpi = 72
        width_inch = width / dpi
        height_inch = height / dpi

        plt.figure(figsize=(width_inch, height_inch), dpi=dpi)
        plt.xlabel('Years')
        plt.ylabel('Occurrences')
        ax = plt.gca()
        fig = Figure()
        ax.set_axisbelow(True)
        ax.yaxis.grid(color='gray', linestyle='dashed')
        df = pd.DataFrame(response_data)
        df.plot(kind='bar', stacked=True, grid=True, ax=ax)
        FigureCanvas(fig)
        buf = io.BytesIO()
        plt.savefig(buf, format='png', bbox_inches='tight')
        plt.close(fig)

        if base_64:
            data_uri = 'data:image/jpg;base64,'
            data_uri += buf.getvalue().encode('base64').replace('\n', '')
            response = HttpResponse(data_uri)
        else:
            response = HttpResponse(buf.getvalue(), content_type='image/png')
        return response


class OccurrencesChartData(APIView):
    """
    Get occurrence data categorized by origin for chart
    """

    def get_data_per_year(self, collection_data, categories):
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
                    if len(category_with_data[category]) < len(year_labels) - 1:
                        category_with_data[category].insert(len(year_labels) - 2, 0)

            category_with_data[data['name']].append(data['count'])

        chart_data['dataset_labels'] = categories
        chart_data['labels'] = year_labels
        chart_data['data'] = category_with_data

        return chart_data

    def get(self, request):
        filters = request.GET.dict()
        search = Search(filters)
        collection_results = search.process_search()
        origin_graph_data = collection_results.annotate(
            year=ExtractYear('collection_date'),
            name=Case(When(category__isnull=False,
                           then=F('category')),
                      default=Value('Unspecified'))
        ).values(
            'year', 'name'
        ).annotate(
            count=Count('year'),
        ).values(
            'year', 'name', 'count'
        ).order_by('year')

        categories = list(collection_results.annotate(
            name=Case(When(category__isnull=False,
                           then=F('category')),
                      default=Value('Unspecified'))
        ).values_list(
            'name', flat=True
        ).distinct('name'))

        result = self.get_data_per_year(origin_graph_data, categories)
        return Response(result)
