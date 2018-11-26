# coding=utf-8
from django.db.models import Q
from rest_framework.views import APIView
from rest_framework.response import Response
from bims.models.biological_collection_record import BiologicalCollectionRecord
from bims.serializers.reference_serializer import ReferenceSerializer
from td_biblio.models import Entry
from bims.api_views.pagination_api_view import PaginationAPIView


class ReferenceList(APIView):
    """Return list of reference"""
    def get(self, request, *args):
        references = \
            BiologicalCollectionRecord.objects.filter(
                    ~Q(reference='') & Q(validated=True)).\
            values_list(
                    'reference', flat=True).\
            distinct()
        results = []
        for reference in references:
            results.append(
                {
                    'reference': reference
                }
            )
        return Response(results)


class ReferenceEntryList(PaginationAPIView):
    """Return list of reference from bibliography apps"""
    queryset = Entry.objects.all()

    def get(self, request, *args):
        page = self.paginate_queryset(self.queryset)
        if page is not None:
            serializer = ReferenceSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        return Response()
