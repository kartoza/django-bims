from django.http import Http404
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response

from bims.models.taxonomy import Taxonomy
from bims.serializers.taxon_serializer import TaxonSimpleSerializer


class AllTaxa(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, *args):
        module = request.GET.get('module', None)
        if not module:
            raise Http404()
        taxa = Taxonomy.objects.filter(taxongroup__id=module).order_by(
            'canonical_name'
        )

        taxon_serializer = TaxonSimpleSerializer(
            taxa,
            many=True
        )

        return Response(taxon_serializer.data)
