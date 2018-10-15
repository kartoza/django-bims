# coding=utf-8
from django.db.models import Q
from rest_framework.views import APIView
from rest_framework.response import Response
from bims.models.biological_collection_record import BiologicalCollectionRecord


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
