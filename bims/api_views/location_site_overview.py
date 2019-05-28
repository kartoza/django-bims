from django.db.models import F, Value, Case, When, Count, Q
from rest_framework.views import APIView
from rest_framework.response import Response
from bims.api_views.search import Search
from bims.models import (
    TaxonGroup,
    BiologicalCollectionRecord,
    IUCNStatus,
    Taxonomy
)
from bims.enums import TaxonomicGroupCategory
from sass.models import SiteVisitTaxon


class MultiLocationSitesOverview(APIView):
    BIODIVERSITY_DATA = 'biodiversity_data'
    MODULE = 'module'
    SASS_EXIST = 'sass_exist'
    GROUP_ICON = 'icon'
    GROUP_OCCURRENCES = 'occurrences'
    GROUP_SITES = 'sites'
    GROUP_ENDEMISM = 'endemism'
    GROUP_NUM_OF_TAXA = 'number_of_taxa'
    GROUP_ORIGIN = 'origin'
    GROUP_CONS_STATUS = 'cons_status'

    def get_all_taxa_children(self, taxa):
        """
        Get all children from taxa
        :param taxa: QuerySet of taxa
        :return: list all children ids
        """
        query = {}
        parent = ''
        or_condition = Q()
        query['id__in'] = list(taxa.values_list('id', flat=True))
        for i in range(6):  # species to class
            parent += 'parent__'
            query[parent + 'in'] = taxa
        for key, value in query.items():
            or_condition |= Q(**{key: value})
        return Taxonomy.objects.filter(or_condition)

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
            group_data[self.MODULE] = group.id

            biodiversity_data[group.name] = group_data

            taxa = group.taxonomies.all()
            taxa_children = self.get_all_taxa_children(taxa)
            taxa_children_ids = list(
                taxa_children.values_list('id', flat=True)
            )

            group_records = collection_results.filter(
                taxonomy__in=taxa_children_ids
            )
            group_records_id = list(group_records.values_list('id', flat=True))
            response_data[self.SASS_EXIST] = (
                SiteVisitTaxon.objects.filter(id__in=group_records_id).exists()
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
            ).order_by('name')
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
            ).order_by('name')
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
            ).order_by('name')
            if all_cons_status:
                category = dict(IUCNStatus.CATEGORY_CHOICES)
                for cons_status in all_cons_status:
                    if cons_status['name'] in category:
                        cons_status['name'] = category[cons_status['name']]
            group_data[self.GROUP_CONS_STATUS] = all_cons_status

        return Response(response_data)
