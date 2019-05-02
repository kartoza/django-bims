# coding=utf-8
from django.db.models import Q
from rest_framework.views import APIView
from rest_framework.response import Response
from bims.models.biological_collection_record import BiologicalCollectionRecord


class SourceCollectionList(APIView):
    """Return list of source collection"""

    def get(self, request, *args):
        sources = (
            BiologicalCollectionRecord.objects.filter(
                ~Q(source_collection='') & Q(
                    validated=True)).distinct().order_by('source_collection')
        )
        return Response(list(sources.values('source_collection')))
