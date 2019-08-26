# coding=utf-8
from rest_framework.views import APIView
from rest_framework.response import Response
from bims.models.source_reference import SourceReference
from bims.serializers.reference_serializer import ReferenceSerializer
from td_biblio.models import Entry
from bims.api_views.pagination_api_view import PaginationAPIView


class ReferenceList(APIView):
    """Return list of reference"""
    def get(self, request, *args):
        references = SourceReference.objects.filter(
            biologicalcollectionrecord__isnull=False,
            biologicalcollectionrecord__validated=True
        )
        results = []
        for reference in references:
            results.append(
                {
                    'id': reference.id,
                    'reference': str(reference.source),
                    'type': reference.reference_type
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
