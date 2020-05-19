# coding=utf-8
from rest_framework.views import APIView
from rest_framework.response import Response
from bims.models.source_reference import LIST_SOURCE_REFERENCES


class ReferenceCategoryList(APIView):
    """Return list of reference category"""
    CATEGORY_LABEL = 'category'

    def get(self, request, *args):
        results = []
        for reference_category, source in LIST_SOURCE_REFERENCES.items():
            results.append(
                {
                    self.CATEGORY_LABEL: reference_category
                }
            )
        return Response(results)
