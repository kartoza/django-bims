# coding=utf-8
import json
from django.http.response import HttpResponse
from rest_framework.views import APIView
from bims.models.biological_collection_record import BiologicalCollectionRecord


class CollectorList(APIView):
    """API for listing all biological collection record collectors."""

    def get(self, request, *args):
        collectors = \
            BiologicalCollectionRecord.objects.filter(
                    validated=True).values_list(
                'collector', flat=True).distinct().order_by('collector')
        return HttpResponse(
            json.dumps(list(collectors)), content_type='application/json')
