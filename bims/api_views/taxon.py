# coding=utf8
from django.http import Http404
from django.contrib.auth.mixins import LoginRequiredMixin
from rest_framework.response import Response
from rest_framework.views import APIView
from bims.models.taxon import Taxon
from bims.models.taxonomy import Taxonomy
from bims.serializers.taxon_serializer import \
    TaxonSerializer, TaxonSimpleSerialializer
from bims.models.biological_collection_record import \
    BiologicalCollectionRecord
from bims.models import TaxonGroup
from bims.api_views.pagination_api_view import PaginationAPIView
from bims.enums.taxonomic_rank import TaxonomicRank
from bims.utils.gbif import suggest_search, process_taxon_identifier


class TaxonSimpleList(PaginationAPIView):
    """
    Retrieve list of taxon
    """
    queryset = Taxon.objects.all().order_by('scientific_name')

    def get(self, request, *args):
        page = self.paginate_queryset(self.queryset)
        if page is not None:
            serializer = TaxonSimpleSerialializer(
                page, many=True)
            return self.get_paginated_response(serializer.data)

        return Response()


class TaxonForDocument(APIView):
    """
    Retrieve taxon for document
    """
    def get(self, request, docid, format=None):
        taxons = Taxon.objects.filter(
            documents__id=docid
        )
        serializer = TaxonSimpleSerialializer(
            taxons, many=True
        )
        return Response(serializer.data)


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
            validated=True,
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
        elif taxon.vernacular_names.all().values().exists():
            common_names = list(taxon.vernacular_names.all().values())
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
                'scientificName': gbif['scientificName'],
                'canonicalName': gbif['canonicalName'],
                'rank': gbif['rank'],
                'key': key,
                'taxaId': taxa_id,
                'source': 'gbif',
                'storedLocal': taxa.exists()
            })

        if not taxon_list:
            # Find from database
            taxa = Taxonomy.objects.filter(
                canonical_name__icontains=taxon_name
            )
            if taxa.exists():
                for taxon in taxa:
                    taxon_list.append({
                        'scientificName': taxon.scientific_name,
                        'canonicalName': taxon.canonical_name,
                        'rank': taxon.rank,
                        'key': taxon.gbif_key,
                        'source': 'local' if not taxon.gbif_key else 'gbif',
                        'storedLocal': True,
                        'taxaId': taxon.id,
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
            try:
                taxon_group = TaxonGroup.objects.get(name=taxon_group)
                if not (
                    taxon_group.taxonomies.filter(taxonomy=taxonomy).exists()
                ):
                    taxon_group.taxonomies.add(taxonomy)
            except TaxonGroup.DoesNotExist:
                pass
        if taxonomy:
            response['id'] = taxonomy.id
            response['taxon_name'] = taxonomy.canonical_name

        return Response(response)
