# coding=utf-8
import json
from django.http.response import HttpResponse
from django.db.models import F
from rest_framework.views import APIView, Response
from bims.utils.river_catchments import get_river_catchment_tree
from bims.models.river_catchment import RiverCatchment


class RiverCatchmentList(APIView):
    """API for listing all endemism"""

    def get(self, request, *args):
        river_catchment_data = get_river_catchment_tree()

        return HttpResponse(
            json.dumps(list(river_catchment_data)),
            content_type='application/json'
        )


class RiverCatchmentTaxonList(APIView):
    """Get taxon list from river catchment"""

    def get(self, request, *args):
        river_catchment = request.GET.get('river_catchment', None)
        if not river_catchment:
            return Response([])

        river_catchment_objects = RiverCatchment.objects.filter(
            value__exact=river_catchment
        )

        if not river_catchment_objects.exists():
            return Response('River catchment not exists')

        taxon_list = []
        for river_catchment_object in river_catchment_objects:
            taxon_list += list(
                river_catchment_object.location_sites.values(
                    taxon_id=F('biological_collection_record__taxonomy'),
                    taxon_name=F(
                        'biological_collection_record__taxonomy__'
                        'scientific_name')
                ).distinct('biological_collection_record__taxonomy')
            )

        return Response(taxon_list)
