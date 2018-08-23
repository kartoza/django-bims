# coding=utf-8
import json
from django.http.response import HttpResponse
from rest_framework.views import APIView
from bims.models.biological_collection_record import BiologicalCollectionRecord


class CategoryList(APIView):
    """API for listing all biological collection record category."""

    def get(self, request, *args):
        category = BiologicalCollectionRecord.CATEGORY_CHOICES
        return HttpResponse(
            json.dumps(list(category)), content_type='application/json')
