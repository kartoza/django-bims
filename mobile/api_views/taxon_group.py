from rest_framework.response import Response
from rest_framework.views import APIView

from bims.models.taxon_group import TaxonGroup
from bims.serializers.taxon_serializer import TaxonGroupSerializer
from bims.enums.taxonomic_group_category import TaxonomicGroupCategory


class TaxonGroupList(APIView):
    """View to return list of taxon group"""
    def get(self, request, *args, **kwargs):
        taxon_group = TaxonGroup.objects.filter(
            category=TaxonomicGroupCategory.SPECIES_MODULE.name
        )
        return Response(TaxonGroupSerializer(
            taxon_group, many=True
        ).data)
