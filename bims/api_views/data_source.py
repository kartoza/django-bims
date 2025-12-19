# coding=utf-8
from rest_framework.views import APIView
from rest_framework.response import Response
from django.utils.decorators import method_decorator
from bims.models import DataSource
from bims.utils.cache import cache_page_with_tag


class DataSourceDescriptionList(APIView):
    """Return list of data sources with their descriptions"""

    def get(self, request, *args):
        data_sources = DataSource.objects.all().values(
            'name', 'category', 'description'
        )

        # Format as a dictionary with name as key
        result = {}
        for ds in data_sources:
            key = ds['name'].lower() if ds['name'] else ''
            if key:
                result[key] = ds['description'] or ''

        return Response(result)
