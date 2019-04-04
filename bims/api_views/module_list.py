# coding=utf-8
from rest_framework.views import APIView
from rest_framework.response import Response
from bims.models.taxon_group import TaxonGroup
from bims.enums.taxonomic_group_category import TaxonomicGroupCategory


class ModuleList(APIView):
    """Return list of species module"""

    def get(self, request, *args):
        species_module = TaxonGroup.objects.filter(
                    category=TaxonomicGroupCategory.SPECIES_MODULE.name
                ).values(
                    'name',
                    'logo',
                    'id'
                )
        return Response(list(species_module))
