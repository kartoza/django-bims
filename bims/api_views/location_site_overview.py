from django.db.models import F, Value, Case, When, Count
from rest_framework.views import APIView
from rest_framework.response import Response
from bims.api_views.search_version_2 import SearchVersion2 as Search
from bims.models import (
    TaxonGroup,
    BiologicalCollectionRecord,
    IUCNStatus
)
from bims.enums import TaxonomicGroupCategory


class MultiLocationSitesOverview(APIView):
    BIODIVERSITY_DATA = 'biodiversity_data'
    GROUP_ICON = 'icon'
    GROUP_OCCURRENCES = 'occurrences'
    GROUP_SITES = 'sites'
    GROUP_ENDEMISM = 'endemism'
    GROUP_NUM_OF_TAXA = 'number_of_taxa'
    GROUP_ORIGIN = 'origin'
    GROUP_CONS_STATUS = 'cons_status'

    def get(self, request):
        """
        Get overview data for multiple sites
        """
        filters = request.GET
        search = Search(filters)
        collection_results = search.process_search()

        response_data = dict()
        biodiversity_data = dict()
        response_data[self.BIODIVERSITY_DATA] = biodiversity_data

        groups = TaxonGroup.objects.filter(
            category=TaxonomicGroupCategory.SPECIES_MODULE.name
        )
        for group in groups:
            group_data = dict()
            group_data[self.GROUP_ICON] = group.logo.name

            biodiversity_data[group.name] = group_data

            taxa = group.taxonomies.all()
            children_ids = []
            for taxon in taxa:
                children = taxon.get_all_children()
                children = children.filter(
                    biologicalcollectionrecord__isnull=False
                ).distinct()
                children_ids.extend(
                    children.values_list('id', flat=True)
                )
            group_records = collection_results.filter(
                taxonomy__id__in=children_ids
            )

            group_data[self.GROUP_OCCURRENCES] = group_records.count()
            group_data[self.GROUP_SITES] = group_records.distinct(
                'site'
            ).count()
            group_data[self.GROUP_NUM_OF_TAXA] = group_records.distinct(
                'taxonomy'
            ).count()
            group_data[self.GROUP_ENDEMISM] = group_records.annotate(
                name=Case(When(taxonomy__endemism__isnull=False,
                               then=F('taxonomy__endemism__name')),
                          default=Value('Unspecified'))
            ).values(
                'name'
            ).annotate(
                count=Count('name')
            ).values(
                'name', 'count'
            )
            group_origins = group_records.annotate(
                name=Case(When(category__isnull=False,
                               then=F('category')),
                          default=Value('Unspecified'))
            ).values(
                'name'
            ).annotate(
                count=Count('name')
            ).values(
                'name', 'count'
            )
            if group_origins:
                category = dict(BiologicalCollectionRecord.CATEGORY_CHOICES)
                for group_origin in group_origins:
                    if group_origin['name'] in category:
                        group_origin['name'] = category[group_origin['name']]
            group_data[self.GROUP_ORIGIN] = group_origins

            all_cons_status = group_records.annotate(
                name=Case(When(taxonomy__iucn_status__isnull=False,
                               then=F('taxonomy__iucn_status__category')),
                          default=Value('Unspecified'))
            ).values(
                'name'
            ).annotate(
                count=Count('name')
            ).values(
                'name', 'count'
            )
            if all_cons_status:
                category = dict(IUCNStatus.CATEGORY_CHOICES)
                for cons_status in all_cons_status:
                    if cons_status['name'] in category:
                        cons_status['name'] = category[cons_status['name']]
            group_data[self.GROUP_CONS_STATUS] = all_cons_status

        return Response(response_data)
