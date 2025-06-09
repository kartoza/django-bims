# coding=utf8
import ast
import logging
import re

from django.contrib.auth import get_user_model
from django.db import transaction, IntegrityError
from django.forms import model_to_dict
from django.http import Http404
from django.db.models import Count, Case, Value, When, F, CharField, Prefetch, Q
from django.contrib.auth.mixins import LoginRequiredMixin
from rest_framework import status
from rest_framework.generics import UpdateAPIView
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.pagination import PageNumberPagination
from taggit.models import Tag

from bims.api_views.taxon_update import is_expert
from bims.models.taxonomy import Taxonomy, TaxonTag, CustomTaggedTaxonomy
from bims.serializers.taxon_detail_serializer import TaxonDetailSerializer
from bims.serializers.taxon_serializer import TaxonSerializer
from bims.models.biological_collection_record import (
    BiologicalCollectionRecord
)
from bims.models import TaxonGroup, VernacularName, TaxonGroupTaxonomy
from bims.enums.taxonomic_rank import TaxonomicRank
from bims.utils.gbif import suggest_search, update_taxonomy_from_gbif, get_vernacular_names
from bims.serializers.tag_serializer import TagSerializer, TaxonomyTagUpdateSerializer
from bims.models.taxonomy_update_proposal import TaxonomyUpdateProposal
from bims.utils.iucn import get_iucn_status

logger = logging.getLogger('bims')

User = get_user_model()


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
                    taxonomy.canonical_name
            }
            taxonomic_rank_values.append(taxonomic_data)
        except KeyError:
            pass
        if taxonomy.parent:
            taxonomic_rank_values += self.get_taxonomic_rank_values(
                taxonomy.parent
            )
        return taxonomic_rank_values

    def get_serializer_data(self, pk):
        taxon = self.get_object(pk)

        serializer = TaxonDetailSerializer(taxon)
        return serializer.data

    def get(self, request, pk, format=None):

        taxon = self.get_object(pk)
        data = self.get_serializer_data(pk)

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
            rank_key = list(rank.keys())[0]
            if rank_key not in data or data[rank_key] == '':
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
            if 'key' not in gbif:
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


class TaxonProposalDetail(TaxonDetail):
    def get_object(self, pk):
        try:
            update_proposal = TaxonomyUpdateProposal.objects.get(pk=pk)
            return update_proposal.original_taxonomy
        except TaxonomyUpdateProposal.DoesNotExist:
            raise Http404

    def get_serializer_data(self, pk):
        serializer = TaxonDetailSerializer(
            TaxonomyUpdateProposal.objects.get(pk=pk)
        )
        return serializer.data


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
        author_name = self.request.POST.get('authorName', '')
        rank = self.request.POST.get('rank', None)
        family_id = self.request.POST.get('familyId', None)
        parent = None
        if family_id:
            parent = Taxonomy.objects.get(id=int(family_id))
        parent_id = self.request.POST.get('parentId', None)
        if parent_id:
            parent = Taxonomy.objects.get(id=int(parent_id))
        if gbif_key:
            taxonomy = update_taxonomy_from_gbif(
                key=gbif_key,
                fetch_parent=True,
                get_vernacular=True
            )
        elif taxon_name and rank:
            if rank.lower() == 'species' and parent and parent.rank.lower() == 'genus':
                if parent.canonical_name not in taxon_name:
                    taxon_name = parent.canonical_name + ' ' + taxon_name
            elif rank.lower() == 'subspecies' and parent and parent.rank.lower() == 'species':
                species_name = parent.species_name
                if species_name not in taxon_name:
                    taxon_name = species_name + ' ' + taxon_name
            taxon_name = taxon_name.strip()
            try:
                taxonomy, created = Taxonomy.objects.get_or_create(
                    scientific_name=taxon_name,
                    canonical_name=taxon_name,
                    rank=rank
                )
            except IntegrityError:
                taxonomy = Taxonomy.objects.get(
                    scientific_name=taxon_name,
                    canonical_name=taxon_name,
                    rank=rank
                )
        if taxon_group_id:
            taxon_group = TaxonGroup.objects.get(id=taxon_group_id)
            taxon_group.taxonomies.add(
                taxonomy,
                through_defaults={
                    'is_validated': False
                }
            )
        else:
            if taxon_group:
                try:
                    taxon_group = TaxonGroup.objects.get(name=taxon_group)
                    taxon_group.taxonomies.add(
                        taxonomy,
                        through_defaults={
                            'is_validated': False
                        }
                    )
                    taxon_group_id = taxon_group.id
                except TaxonGroup.DoesNotExist:
                    pass
        if taxonomy:
            response['id'] = taxonomy.id
            response['taxon_name'] = taxonomy.canonical_name

            if author_name:
                taxonomy.author = author_name
                taxonomy.save()

            # Check if it's a new taxonomy
            if not TaxonGroupTaxonomy.objects.filter(
                    taxonomy=taxonomy,
                    taxongroup=taxon_group,
                    is_validated=True).exists():
                taxonomy.owner = self.request.user
                taxonomy.ready_to_be_validate()
                taxonomy.send_new_taxon_email(taxon_group_id)

            if parent:
                taxonomy.parent = parent
                taxonomy.save()

        with transaction.atomic():
            taxonomy_data = model_to_dict(
                taxonomy,
                exclude=[
                    'id',
                    'iucn_status',
                    'vernacular_names',
                    'author',
                    'tags',
                    'biographic_distributions',
                    'owner',
                    'parent'])
            taxonomy_update_proposal, created = (
                TaxonomyUpdateProposal.objects.get_or_create(
                    original_taxonomy=taxonomy,
                    taxon_group=taxon_group,
                    status='pending',
                    new_data=True,
                    owner=taxonomy.owner,
                    parent=taxonomy.parent,
                    taxon_group_under_review=taxon_group,
                    author=author_name,
                    iucn_status=taxonomy.iucn_status,
                    **taxonomy_data
                )
            )
            if created:
                vernacular_names_instances = list(taxonomy.vernacular_names.all())
                taxonomy_update_proposal.vernacular_names.set(vernacular_names_instances)

        return Response(response)


class TaxaPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'


def split_authors(author_string):
    regex = r'"(.*?)"'
    matches = re.findall(regex, author_string)
    decoded_matches = [match for match in matches]
    return decoded_matches


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
        tag_filter_type = request.GET.get('tagFT', 'OR')
        cons_status = request.GET.get('cons_status', '').split(',')
        cons_status = list(filter(None, cons_status))
        endemism = request.GET.get('endemism', '').split(',')
        endemism = list(filter(None, endemism))
        taxonomic_status = request.GET.get('taxonomic_status', '').split(',')
        taxonomic_status = list(filter(None, taxonomic_status))
        taxon_name = request.GET.get('taxon', '').strip()
        is_gbif = request.GET.get('is_gbif', '')
        is_iucn = request.GET.get('is_iucn', '')
        validated = request.GET.get('validated', 'True')
        order = request.GET.get('o', '')
        author_names = request.GET.get('author', '')
        family_name = request.GET.get('family', '')
        genus_name = request.GET.get('genus', '')
        species_name = request.GET.get('species', '')
        summary_only = request.GET.get('summary', 'False') == 'True'
        taxon_group_ids = None

        authors = []
        if author_names:
            authors = split_authors(author_names)

        biodiversity_distributions = (
            request.GET.get('bD', '').split(',')
        )
        biodiversity_distributions = (
            list(filter(None, biodiversity_distributions))
        )
        biodiversity_distributions_filter_type = (
            request.GET.get('bDFT', 'OR')
        )

        if order == 'endemism_name':
            order = 'endemism__name'

        if 'accepted_taxonomy_name' in order:
            order = order.replace(
                'accepted_taxonomy_name',
                'accepted_taxonomy__canonical_name'
            )

        # Filter by parent
        parent_ids = request.GET.get('parent', '').split(',')
        parent_ids = list(filter(None, parent_ids))
        id = request.GET.get('id', '')
        if id:
            return Taxonomy.objects.filter(id=id)

        if taxon_group_id:
            try:
                taxon_group = TaxonGroup.objects.get(id=taxon_group_id)
            except TaxonGroup.DoesNotExist:
                raise Http404('Taxon group does not exist')
        else:
            taxon_group = None

        taxon_list = Taxonomy.objects.all()

        if parent_ids:
            parents = Taxonomy.objects.filter(
                Q(id__in=parent_ids)
            )
            if parents.exists():
                taxon_list = parents.first().get_all_children()
            else:
                taxon_list = parents

        if taxon_group:
            taxon_group_ids = TaxaList.get_descendant_group_ids(
                taxon_group)
            taxon_list = taxon_list.filter(
                taxongroup__id__in=taxon_group_ids,
                taxongrouptaxonomy__is_rejected=False,
            ).distinct().order_by('canonical_name')
        else:
            taxon_list = taxon_list.filter(
                taxongrouptaxonomy__is_rejected=False,
            ).distinct().order_by('canonical_name')

        if len(authors) > 0:
            taxon_list = taxon_list.filter(
                author__in=authors
            )

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
        if len(taxonomic_status) > 0:
            queries = Q()
            for status in taxonomic_status:
                queries |= Q(taxonomic_status__iexact=status)
            taxon_list = taxon_list.filter(queries)
        if taxon_name:
            taxon_list = taxon_list.filter(
                Q(canonical_name__icontains=taxon_name) |
                Q(accepted_taxonomy__canonical_name__icontains=taxon_name)
            )
        if family_name:
            taxon_list = taxon_list.filter(
                hierarchical_data__family_name__icontains=family_name
            )
        if genus_name:
            taxon_list = taxon_list.filter(
                hierarchical_data__genus_name__icontains=genus_name
            )
        if species_name:
            taxon_list = taxon_list.filter(
                hierarchical_data__species_name__icontains=species_name
            )

        if tags:
            taxon_list = taxon_list.prefetch_related(
                'tags',
            )
            if tag_filter_type == 'AND':
                for tag in tags:
                    taxon_list = taxon_list.filter(tags__name=tag)
            else:
                taxon_list = taxon_list.filter(
                    tags__name__in=tags
                ).distinct()
        if biodiversity_distributions:
            taxon_list = taxon_list.prefetch_related(
                'biographic_distributions'
            )
            if biodiversity_distributions_filter_type == 'AND':
                for b_tag in biodiversity_distributions:
                    taxon_list = taxon_list.filter(
                        customtaggedtaxonomy__tag__name=b_tag
                    )
            else:
                taxon_list = taxon_list.filter(
                    customtaggedtaxonomy__tag__name__in=biodiversity_distributions
                ).distinct()
        if validated:
            try:
                validated = ast.literal_eval(validated.replace('/', ''))
                if not validated:
                    # Check if the user is a superuser or has expert permissions for the taxon group
                    is_user_expert = is_expert(
                        request.user,
                        TaxonGroup.objects.get(id=taxon_group_id)
                    )
                    if request.user.is_superuser or is_user_expert:
                        validated_filters = {
                            'taxongrouptaxonomy__is_validated': False,
                        }
                    else:
                        taxon_list = taxon_list.none()
                        return taxon_list
                else:
                    validated_filters = {
                        'taxongrouptaxonomy__is_validated': True,
                    }
                if taxon_group_ids:
                    validated_filters[
                        'taxongrouptaxonomy__taxongroup__in'
                    ] = taxon_group_ids
                taxon_list = taxon_list.filter(
                    **validated_filters
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
        if order and not summary_only:
            if 'total_records' in order:
                taxon_list = taxon_list.annotate(
                    total_records=Count('biologicalcollectionrecord')
                ).order_by(order)
            elif 'family' in order or 'species' in order or 'genus' in order:
                rank_name = order.split('-')[-1]

                taxon_list = taxon_list.annotate(
                    **{rank_name: F(f'hierarchical_data__{rank_name}_name')}
                ).annotate(
                        order_priority=Case(
                            When(**{f"{rank_name}__isnull": False}, then=Value(0)),
                            When(**{f"{rank_name}__exact": ''}, then=Value(1)),
                            default=Value(1),
                            output_field=CharField(),
                        )
                    ).order_by('order_priority', order, 'id')
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
        summary_only = request.GET.get('summary', 'False') == 'True'

        if summary_only:
            return Response(list(TaxonGroupTaxonomy.objects.filter(
                taxonomy__in=taxon_list
            ).values('taxongroup', 'taxongroup__name').annotate(
                total=Count('taxongroup'))))

        self.pagination_class.page_size = request.GET.get('page_size', 20)
        page = self.paginate_queryset(taxon_list)
        validated = ast.literal_eval(request.GET.get('validated', 'True'))
        if page is not None:
            taxon_group_id = request.GET.get('taxonGroup', None)
            serializer = self.get_paginated_response(
                TaxonSerializer(page, many=True, context={
                    'taxon_group_id': taxon_group_id,
                    'user': request.user.id,
                    'validated': validated
                }).data)
            serializer.data['is_expert'] = is_expert(
                self.request.user,
                TaxonGroup.objects.get(id=taxon_group_id)
            ) if taxon_group_id else False
        else:
            serializer = TaxonSerializer(
                taxon_list,
                many=True,
                context={
                    'user': request.user.id
                }
            )
        return Response(serializer.data)


class TaxonTagAutocompleteAPIView(APIView):
    def get(self, request, format=None):
        query = request.query_params.get('q', '')
        biographic = ast.literal_eval(request.query_params.get('biographic', 'False'))
        if biographic:
            taxonomy_tags = TaxonTag.objects.filter(
                name__icontains=query
            ).distinct()[:10]
        else:
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


class IUCNStatusFetchView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request, *args, **kwargs):
        taxonomy_id = self.kwargs.get('pk')

        if not taxonomy_id:
            return Response(
                {"detail": "Missing taxon_id"},
                status=status.HTTP_400_BAD_REQUEST)

        taxon = Taxonomy.objects.get(id=taxonomy_id)
        iucn_status, sis_id, iucn_url = get_iucn_status(taxon)

        if iucn_status:
            return Response({
                "status_category": iucn_status.category,
                "sis_id": sis_id,
                "iucn_url": iucn_url
            })
        return Response(
            {"detail": "Not found"},
            status=status.HTTP_404_NOT_FOUND)
