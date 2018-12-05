from django.db.models import Q
from rest_framework.response import Response
from geonode.documents.models import Document
from bims.api_views.pagination_api_view import PaginationAPIView
from bims.serializers.document_serializer import DocumentSerializer


class DocumentList(PaginationAPIView):
    """Return list of reference from bibliography apps"""

    def get(self, request, *args):
        queryset = Document.objects.filter(
            Q(owner=self.request.user) |
            Q(group__in=self.request.user.groups.values_list(
                'id', flat=True))
        )
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = DocumentSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        return Response()
