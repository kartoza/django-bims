# coding=utf8
import ast
import logging

from django.db import transaction
from django.http import Http404
from django.db.models import Count
from django.contrib.auth.mixins import LoginRequiredMixin
from rest_framework.generics import UpdateAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.pagination import PageNumberPagination
from taggit.models import Tag

from bims.models.taxonomy import Taxonomy
from bims.serializers.taxon_serializer import TaxonSerializer
from bims.models.biological_collection_record import (
    BiologicalCollectionRecord
)
from bims.models import TaxonGroup, VernacularName
from bims.enums.taxonomic_rank import TaxonomicRank
from bims.utils.gbif import suggest_search, update_taxonomy_from_gbif, get_vernacular_names
from bims.serializers.tag_serializer import TagSerializer, TaxonomyTagUpdateSerializer
from bims.models.taxonomy_update_proposal import TaxonomyUpdateProposal

logger = logging.getLogger('bims')


class TaxonDetail(APIView):
    """
    Retrieve a taxon instance.
    """

    def get_object(self, pk):
        try:
            return Taxonomy.objects.get(pk=pk)
        except Taxonomy.DoesNotExist:
            raise Http404

    def get_taxonomic_rank_values(self, taxonomy):
        taxonomic_rank_values = []
        try:
            taxonomic_data = {
                TaxonomicRank[taxonomy.rank].value.lower():
                    taxonomy.scientific_name
            }
            taxonomic_rank_values.append(taxonomic_data)
        except KeyError:
            pass
        if taxonomy.parent:
            taxonomic_rank_values += self.get_taxonomic_rank_values(
                taxonomy.parent
            )
        return taxonomic_rank_values

    def get(self, request, pk, format=None):

        taxon = self.get_object(pk)

        serializer = TaxonSerializer(taxon)
        data = serializer.data

        records = BiologicalCollectionRecord.objects.filter(
            taxonomy=taxon
        )

        # Endemism
        if taxon.endemism:
            data['endemism'] = taxon.endemism.name

        # Origins
        origin_value = ''
        origin = records.values_list('taxonomy__origin', flat=True).distinct()
        if origin:
            for category in Taxonomy.CATEGORY_CHOICES:
                if category[0] == origin[0]:
                    origin_value = category[1]
        data['origin'] = origin_value

        data['count'] = records.count()
        data['total_sites'] = records.distinct('site').count()

        # Taxonomic rank tree
        taxonomic_rank = self.get_taxonomic_rank_values(taxon)
        for rank in taxonomic_rank:
            data.update(rank)
        common_names = []
        results = []

        # Common name
        if taxon.vernacular_names.exists():
            common_names = list(
                taxon.vernacular_names.filter(language='eng').values_list('name', flat=True))
        if len(common_names) == 0:
            vernacular_names = get_vernacular_names(taxon.gbif_key)
            if vernacular_names:
                results = vernacular_names['results']
            if len(results) == 0:
                data['common_name'] = 'Unknown'
            else:
                for result in results:
                    if 'language' in result and result['language'] == 'eng':
                        fields = {'language': result['language']}
                        data['common_name'] = result['vernacularName']
                        if 'source' in result:
                            fields['source'] = result['source']
                        if 'taxonKey' in result:
                            fields['taxon_key'] = int(result['taxonKey'])
                        vernacular_name, status = (
                            VernacularName.objects.get_or_create(
                                name=result['vernacularName'],
                                **fields
                            )
                        )
                        taxon.vernacular_names.add(vernacular_name)
                        break
        else:
            data['common_name'] = common_names[0]

        return Response(data)


class FindTaxon(APIView):
    """
    Find taxon in gbif and local database
    """
    limit_default = 20
    scientific_name = 'scientificName'
    canonical_name = 'canonicalName'
    rank = 'rank'
    key = 'key'
    taxa_id = 'taxaId'
    source = 'source'
    stored_local = 'storedLocal'
    validated = 'validated'
    taxon_group_ids = 'taxonGroupIds'
    status = 'status'

    def get(self, request, *args):
        taxon_list = []
        taxon_key = []
        phylum_keys = []

        query_dict = request.GET.dict()

        # Find classes to narrow down the results
        taxon_group = query_dict.get('taxonGroup', None)
        taxon_group_id = query_dict.get('taxonGroupId', None)
        taxon_name = query_dict.get('q', None)
        if taxon_group:
            del query_dict['taxonGroup']
            try:
                taxon_group = TaxonGroup.objects.get(name=taxon_group)
                phylum_keys = list(taxon_group.taxonomies.filter(
                    parent__rank=TaxonomicRank.PHYLUM
                ).values_list('parent__gbif_key', flat=True))
            except (
                    TaxonGroup.DoesNotExist,
                    TaxonGroup.MultipleObjectsReturned):
                pass

        if taxon_group_id:
            del query_dict['taxonGroupId']
            try:
                taxon_group = TaxonGroup.objects.get(id=taxon_group_id)
                phylum_keys = list(taxon_group.taxonomies.filter(
                    parent__rank=TaxonomicRank.PHYLUM
                ).values_list('parent__gbif_key', flat=True))
            except (
                    TaxonGroup.DoesNotExist,
                    TaxonGroup.MultipleObjectsReturned):
                pass

        if 'limit' not in query_dict:
            # If the limit is not set, we set the default limit to 20
            query_dict['limit'] = self.limit_default
        gbif_response = suggest_search(query_dict)

        for gbif in gbif_response:
            if 'key' not in gbif or 'phylumKey' not in gbif:
                continue
            if phylum_keys and gbif['phylumKey'] not in phylum_keys:
                continue
            key = gbif['key']
            if key in taxon_key:
                continue
            taxa = Taxonomy.objects.filter(gbif_key=key)
            taxa_id = ''
            validated = False
            taxon_group_ids = []
            status = gbif['status']
            if taxa.exists():
                taxon = taxa.first()
                taxa_id = taxon.id
                validated = taxon.validated
                taxon_group_ids = taxon.taxongroup_set.all().values_list(
                    'id', flat=True
                )
                status = taxon.taxonomic_status
            try:
                canonicalName = gbif['canonicalName']
            except KeyError:
                canonicalName = gbif['scientificName']
            taxon_list.append({
                self.scientific_name: gbif['scientificName'],
                self.canonical_name: canonicalName,
                self.rank: gbif['rank'],
                self.key: key,
                self.taxa_id: taxa_id,
                self.source: 'gbif',
                self.stored_local: taxa.exists(),
                self.validated: validated,
                self.taxon_group_ids: taxon_group_ids,
                self.status: status
            })

        if not taxon_list:
            # Find from database
            taxa = Taxonomy.objects.filter(
                canonical_name__icontains=taxon_name
            )
            if taxa.exists():
                for taxon in taxa:
                    taxon_list.append({
                        self.scientific_name: taxon.scientific_name,
                        self.canonical_name: taxon.canonical_name,
                        self.rank: taxon.rank,
                        self.key: taxon.gbif_key,
                        self.source: 'local' if not taxon.gbif_key else 'gbif',
                        self.stored_local: True,
                        self.taxa_id: taxon.id,
                        self.validated: taxon.validated,
                        self.taxon_group_ids: [],
                        self.status: taxon.taxonomic_status
                    })

        return Response(taxon_list)


class AddNewTaxon(LoginRequiredMixin, APIView):
    """Add new taxon, then return the id of newly created taxon"""

    def post(self, request, *args):
        response = {
            'id': '',
            'taxon_name': '',
        }
        taxonomy = None
        gbif_key = self.request.POST.get('gbifKey', None)
        taxon_name = self.request.POST.get('taxonName', None)
        taxon_group = self.request.POST.get('taxonGroup', None)
        taxon_group_id = self.request.POST.get('taxonGroupId', None)
        rank = self.request.POST.get('rank', None)
        family_id = self.request.POST.get('familyId', None)
        family = None
        if family_id:
            family = Taxonomy.objects.get(id=int(family_id))
        if gbif_key:
            taxonomy = update_taxonomy_from_gbif(
                key=gbif_key,
                fetch_parent=True,
                get_vernacular=True
            )
        elif taxon_name and rank:
            taxonomy, created = Taxonomy.objects.get_or_create(
                scientific_name=taxon_name,
                canonical_name=taxon_name,
                rank=rank
            )
        if taxon_group_id:
            taxon_group = TaxonGroup.objects.get(id=taxon_group_id)
            taxon_group.taxonomies.add(taxonomy)
        else:
            if taxon_group:
                try:
                    taxon_group = TaxonGroup.objects.get(name=taxon_group)
                    taxon_group.taxonomies.add(taxonomy)
                except TaxonGroup.DoesNotExist:
                    pass
        if taxonomy:
            response['id'] = taxonomy.id
            response['taxon_name'] = taxonomy.canonical_name

            # Check if it's a new taxonomy
            if not taxonomy.validated:
                taxonomy.owner = self.request.user
                taxonomy.ready_to_be_validate()
                taxonomy.send_new_taxon_email(taxon_group_id)

            if family:
                taxonomy.parent = family
                taxonomy.save()

        with transaction.atomic():
            TaxonomyUpdateProposal.objects.get_or_create(
                original_taxonomy=taxonomy,
                taxon_group=taxon_group,
                status='pending',
                scientific_name=taxonomy.scientific_name,
                canonical_name=taxonomy.canonical_name
            )

        return Response(response)


class TaxaPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'


class TaxaList(LoginRequiredMixin, APIView):
    """Returns list of taxa filtered by taxon group"""
    pagination_class = TaxaPagination

    @staticmethod
    def get_descendant_group_ids(taxon_group):
        """Recursively collect all descendant group IDs"""
        group_ids = [taxon_group.id]
        child_groups = TaxonGroup.objects.filter(
            parent=taxon_group)
        for child in child_groups:
            group_ids.extend(TaxaList.get_descendant_group_ids(
                child))
        return group_ids

    @staticmethod
    def get_taxa_by_parameters(request):
        taxon_group_id = request.GET.get('taxonGroup', '')
        rank = request.GET.get('rank', '')
        ranks = request.GET.get('ranks', '').split(',')
        ranks = list(filter(None, ranks))
        origins = request.GET.get('origins', '').split(',')
        origins = list(filter(None, origins))
        tags = request.GET.get('tags', '').split(',')
        tags = list(filter(None, tags))
        cons_status = request.GET.get('cons_status', '').split(',')
        cons_status = list(filter(None, cons_status))
        endemism = request.GET.get('endemism', '').split(',')
        endemism = list(filter(None, endemism))
        taxon_name = request.GET.get('taxon', '')
        is_gbif = request.GET.get('is_gbif', '')
        is_iucn = request.GET.get('is_iucn', '')
        validated = request.GET.get('validated', 'True')
        order = request.GET.get('o', '')
        # Filter by parent
        parent_ids = request.GET.get('parent', '').split(',')
        parent_ids = list(filter(None, parent_ids))
        id = request.GET.get('id', '')
        if id:
            return Taxonomy.objects.filter(id=id)
        if not taxon_group_id:
            raise Http404('Missing taxon group id')
        try:
            taxon_group = TaxonGroup.objects.get(id=taxon_group_id)
        except TaxonGroup.DoesNotExist:
            raise Http404('Taxon group does not exist')

        taxon_group_ids = TaxaList.get_descendant_group_ids(
            taxon_group)
        taxon_list = Taxonomy.objects.filter(
            taxongroup__id__in=taxon_group_ids,
            taxongrouptaxonomy__is_rejected=False,
        ).distinct().order_by('canonical_name')

        if parent_ids:
            parents = taxon_list.filter(id__in=parent_ids)
            if parents.exists():
                taxon_list = parents[0].get_all_children()
            else:
                taxon_list = parents
        if rank:
            taxon_list = taxon_list.filter(rank=rank)
        if len(ranks) > 0:
            taxon_list = taxon_list.filter(
                rank__in=ranks
            )
        if len(origins) > 0:
            taxon_list = taxon_list.filter(
                origin__in=origins
            )
        if len(cons_status) > 0:
            taxon_list = taxon_list.filter(
                iucn_status__category__in=cons_status
            )
        if len(endemism) > 0:
            taxon_list = taxon_list.filter(
                endemism__name__in=endemism
            )
        if taxon_name:
            taxon_list = taxon_list.filter(
                canonical_name__icontains=taxon_name
            )
        if tags:
            taxon_list = taxon_list.filter(
                tags__name__in=tags
            ).distinct()
        if validated:
            try:
                validated = ast.literal_eval(validated.replace('/', ''))
                if not validated:
                    taxon_list = taxon_list.exclude(
                        taxongrouptaxonomy__is_validated=True,
                        taxongrouptaxonomy__taxongroup__in=taxon_group_ids
                    )
                else:
                    taxon_list = taxon_list.filter(
                        taxongrouptaxonomy__is_validated=True,
                        taxongrouptaxonomy__taxongroup__in=taxon_group_ids
                    )
            except ValueError:
                pass
        if is_gbif:
            try:
                is_gbif = ast.literal_eval(is_gbif)
                if is_gbif:
                    taxon_list = taxon_list.exclude(
                        gbif_key__isnull=True
                    )
                else:
                    taxon_list = taxon_list.filter(
                        gbif_key__isnull=True
                    )
            except ValueError:
                pass
        if is_iucn:
            try:
                is_iucn = ast.literal_eval(is_iucn)
                if is_iucn:
                    taxon_list = taxon_list.exclude(
                        iucn_redlist_id__isnull=True
                    )
                else:
                    taxon_list = taxon_list.filter(
                        iucn_redlist_id__isnull=True
                    )
            except ValueError:
                pass
        if order:
            if 'total_records' in order:
                taxon_list = taxon_list.annotate(
                    total_records=Count('biologicalcollectionrecord')
                ).order_by(order)
            elif 'origin' not in order:
                taxon_list = taxon_list.order_by(order)
            else:
                origin_order = [
                    'indigenous',
                    'alien',
                    'alien-invasive',
                    'alien-non-invasive',
                    'unknown',
                    ''
                ]
                if '-' in order:
                    origin_order.reverse()
                taxon_list = sorted(
                    taxon_list,
                    key=lambda x: origin_order.index(x.origin)
                )
        return taxon_list

    @property
    def paginator(self):
        if not hasattr(self, '_paginator'):
            if self.pagination_class is None:
                self._paginator = None
            else:
                self._paginator = self.pagination_class()
        else:
            pass
        return self._paginator

    def paginate_queryset(self, queryset):

        if self.paginator is None:
            return None
        return self.paginator.paginate_queryset(
            queryset,
            self.request,
            view=self)

    def get_paginated_response(self, data):
        assert self.paginator is not None
        return self.paginator.get_paginated_response(data)

    def get(self, request, *args):
        taxon_list = self.get_taxa_by_parameters(request)
        page = self.paginate_queryset(taxon_list)
        if page is not None:
            serializer = self.get_paginated_response(
                TaxonSerializer(page, many=True, context={
                    'taxon_group_id': request.GET.get('taxonGroup', None)
                }).data)
        else:
            serializer = TaxonSerializer(taxon_list, many=True)
        return Response(serializer.data)


class TaxonTagAutocompleteAPIView(APIView):
    def get(self, request, format=None):
        query = request.query_params.get('q', '')
        taxonomy_tags = Tag.objects.filter(
            taxonomy__isnull=False,
            name__icontains=query
        ).distinct()[:10]
        serializer = TagSerializer(taxonomy_tags, many=True)
        return Response(serializer.data)


class AddTagAPIView(UpdateAPIView):
    queryset = Taxonomy.objects.all()
    serializer_class = TaxonomyTagUpdateSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        taxonomy_id = self.kwargs.get('pk')
        return Taxonomy.objects.get(pk=taxonomy_id)
