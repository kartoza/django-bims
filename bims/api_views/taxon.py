# coding=utf8
from django.http import Http404
from django.contrib.auth.mixins import LoginRequiredMixin
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.pagination import PageNumberPagination
from bims.models.taxonomy import Taxonomy
from bims.serializers.taxon_serializer import TaxonSerializer
from bims.models.biological_collection_record import (
    BiologicalCollectionRecord
)
from bims.models import TaxonGroup
from bims.enums.taxonomic_rank import TaxonomicRank
from bims.utils.gbif import suggest_search, process_taxon_identifier


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
        origin = records.values_list('category', flat=True).distinct()
        if origin:
            for category in BiologicalCollectionRecord.CATEGORY_CHOICES:
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

        # Common name
        if taxon.vernacular_names.filter(language='eng').exists():
            common_names = list(
                taxon.vernacular_names.all().filter(language='eng').values())
        if len(common_names) == 0:
            data['common_name'] = 'Unknown'
        else:
            data['common_name'] = str(common_names[0]['name']).capitalize()

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

    def get(self, request, *args):
        taxon_list = []
        taxon_key = []
        phylum_keys = []

        query_dict = request.GET.dict()

        # Find classes to narrow down the results
        taxon_group = query_dict.get('taxonGroup', None)
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
            if taxa.exists():
                taxa_id = taxa[0].id
            taxon_list.append({
                self.scientific_name: gbif['scientificName'],
                self.canonical_name: gbif['canonicalName'],
                self.rank: gbif['rank'],
                self.key: key,
                self.taxa_id: taxa_id,
                self.source: 'gbif',
                self.stored_local: taxa.exists()
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
        rank = self.request.POST.get('rank', None)
        if gbif_key:
            taxonomy = process_taxon_identifier(
                key=gbif_key,
                fetch_parent=True,
                get_vernacular=False
            )
        elif taxon_name and rank:
            taxonomy, created = Taxonomy.objects.get_or_create(
                scientific_name=taxon_name,
                canonical_name=taxon_name,
                rank=rank
            )
            if taxon_group:
                try:
                    taxon_group = TaxonGroup.objects.get(name=taxon_group)
                    taxon_group.taxonomies.add(taxonomy)
                except TaxonGroup.DoesNotExist:
                    pass
        if taxonomy:
            response['id'] = taxonomy.id
            response['taxon_name'] = taxonomy.canonical_name

        return Response(response)


class TaxaPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'


class TaxaList(LoginRequiredMixin, APIView):
    """Returns list of taxa filtered by taxon group"""
    pagination_class = TaxaPagination

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
        taxon_group_id = request.GET.get('taxonGroup', '')
        rank = request.GET.get('rank', '')
        taxon_name = request.GET.get('taxon', '')
        if not taxon_group_id:
            raise Http404('Missing taxon group id')
        try:
            taxon_group = TaxonGroup.objects.get(id=taxon_group_id)
        except TaxonGroup.DoesNotExist:
            raise Http404('Taxon group does not exist')
        taxon_list = taxon_group.taxonomies.all()
        if rank:
            taxon_list = taxon_list.filter(rank=rank)
        if taxon_name:
            taxon_list = taxon_list.filter(
                canonical_name__icontains=taxon_name
            )
        page = self.paginate_queryset(taxon_list)
        if page is not None:
            serializer = self.get_paginated_response(
                TaxonSerializer(page, many=True).data)
        else:
            serializer = TaxonSerializer(taxon_list, many=True)
        return Response(serializer.data)
