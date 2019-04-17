from rest_framework.views import APIView
from rest_framework.response import Response
from django.db.models import Count, Q, F, Case, When, Value
from bims.models import (
    TaxonGroup,
    BiologicalCollectionRecord,
)
from bims.enums.taxonomic_group_category import TaxonomicGroupCategory


class ModuleSummary(APIView):
    """
    Summary for species module created in TaxonGroup
    """

    def get(self, request, *args):
        response_data = dict()
        taxon_groups = TaxonGroup.objects.filter(
            category=TaxonomicGroupCategory.SPECIES_MODULE.name,
            name__icontains='fish'
        )
        for taxon_group in taxon_groups:
            taxa = taxon_group.taxonomies.all()
            response_data[taxon_group.name] = dict()
            for taxon in taxa:
                modules_query = Q()
                children = taxon.get_all_children()
                children = children.filter(
                    biologicalcollectionrecord__isnull=False
                ).distinct()
                if children:
                    modules_query = Q(
                        **{'taxonomy__in': children}
                    )
                collections = BiologicalCollectionRecord.objects.filter(
                    modules_query
                )
                response_data[taxon_group.name][taxon.scientific_name] = dict(
                    collections.annotate(
                        value=Case(When(category__isnull=False,
                                        then=F('category')),
                                   default=Value('Unspecified'))
                    ).values('value').annotate(
                        count=Count('value')
                    ).values_list('value', 'count')
                )
                response_data[taxon_group.name][taxon.scientific_name][
                    'total'] = collections.count()
                response_data[taxon_group.name][taxon.scientific_name][
                    'total_site'] = (
                    collections.distinct('site').count()
                )
        return Response(response_data)
