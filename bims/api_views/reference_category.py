# coding=utf-8
from django.db.models import Q
from rest_framework.views import APIView
from rest_framework.response import Response
from bims.models.biological_collection_record import BiologicalCollectionRecord


class ReferenceCategoryList(APIView):
    """Return list of reference category"""
    def get(self, request, *args):
        reference_category = \
            BiologicalCollectionRecord.objects.filter(
                    ~Q(reference_category='') & Q(validated=True)).\
            values_list(
                    'reference_category', flat=True).\
            distinct().order_by('reference_category')
        results = []
        contain_thesis = False
        for reference in reference_category:
            # Merge thesis
            if 'thesis' in reference.lower():
                if not contain_thesis:
                    reference = 'Thesis'
                    contain_thesis = True
                else:
                    continue
            results.append(
                {
                    'category': reference
                }
            )
        return Response(results)
