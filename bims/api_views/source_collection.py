# coding=utf-8
from django.contrib.sites.models import Site
from django.db.models import Q
from django.utils.decorators import method_decorator
from rest_framework.views import APIView
from rest_framework.response import Response
from bims.models.biological_collection_record import BiologicalCollectionRecord
from bims.utils.cache import cache_page_with_tag

SOURCE_COLLECTION_LIST = 'source_collection_list'


class SourceCollectionList(APIView):
    """Return list of source collection"""

    @method_decorator(
        cache_page_with_tag(60 * 60 * 24, SOURCE_COLLECTION_LIST))
    def get(self, request, *args):
        sources = (
            BiologicalCollectionRecord.objects.filter(
                ~Q(source_collection='')
            ).order_by('source_collection').values(
                'source_collection'
            ).distinct()
        )
        return Response(list(sources))
