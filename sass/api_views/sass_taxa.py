from bims.enums.taxonomic_group_category import TaxonomicGroupCategory

from bims.models.taxon_group import TaxonGroup
from rest_framework.response import Response
from rest_framework.views import APIView

from bims.models import Taxonomy
from sass.models.sass_taxon import SassTaxon


class SassTaxaListApi(APIView):
    """
    List all taxa for SASS data
    """

    def get(self, *args, **kwargs):
        sass_taxon_list = SassTaxon.objects.filter(
            sass_5_score__isnull=False).order_by(
            'display_order_sass_5'
        )
        sass_taxa = {}
        for sass_taxon in sass_taxon_list:
            taxonomies = Taxonomy.objects.filter(
                canonical_name__icontains=sass_taxon.taxon.canonical_name
            )
            try:
                group = (
                    TaxonGroup.objects.filter(
                        taxonomies__in=list(
                            taxonomies.values_list('id', flat=True)),
                        category=TaxonomicGroupCategory.SASS_TAXON_GROUP.name
                    )[0].name
                )
            except IndexError:
                continue
            if group not in sass_taxa:
                sass_taxa[group] = []
            sass_taxa[group].append(
                sass_taxon.taxon_sass_4
                if sass_taxon.taxon_sass_4
                else sass_taxon.taxon_sass_5)
        return Response(sass_taxa)
