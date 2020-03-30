# coding=utf-8
from rest_framework.views import APIView
from rest_framework.response import Response
from bims.serializers.reference_serializer import ReferenceSerializer
from td_biblio.models import Entry
from bims.api_views.pagination_api_view import PaginationAPIView
from bims.tasks.source_reference import get_source_reference_filter


class ReferenceList(APIView):
    """Return list of reference"""
    def get(self, request, *args):
        return Response(get_source_reference_filter())


class ReferenceEntryList(PaginationAPIView):
    """Return list of reference from bibliography apps"""
    queryset = Entry.objects.all()

    def get(self, request, *args):
        page = self.paginate_queryset(self.queryset)
        if page is not None:
            serializer = ReferenceSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        return Response()
