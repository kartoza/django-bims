import json
from django.contrib.auth.mixins import UserPassesTestMixin
from django.http import Http404
from rest_framework.response import Response
from rest_framework.views import APIView
from bims.models import TaxonGroup, Taxonomy, BiologicalCollectionRecord


def update_taxon_group_orders(taxon_group_ids):
    """
    Update taxon group orders
    :param taxon_group_ids: list of taxon taxon group ids
    """
    taxon_groups = TaxonGroup.objects.filter(
        id__in=taxon_group_ids
    )
    for taxon_group in taxon_groups:
        try:
            order = taxon_group_ids.index(taxon_group.id)
            taxon_group.display_order = order
            taxon_group.save()
        except ValueError:
            continue


def remove_taxa_from_taxon_group(taxa_ids, taxon_group_id):
    """
    Remove taxa from taxon group
    :param taxa_ids: list of taxon taxon ids
    :param taxon_group_id: id of the taxon group
    """
    taxa = Taxonomy.objects.filter(
        id__in=taxa_ids
    )
    try:
        taxon_group = TaxonGroup.objects.get(
            id=taxon_group_id
        )
    except TaxonGroup.DoesNotExist:
        return
    for taxonomy in taxa:
        taxon_group.taxonomies.remove(taxonomy)
        BiologicalCollectionRecord.objects.filter(
            taxonomy=taxonomy
        ).update(module_group=None)


def add_taxa_to_taxon_group(taxa_ids, taxon_group_id):
    """
    Add taxa to taxon group
    :param taxa_ids: list of taxon taxon ids
    :param taxon_group_id: id of the taxon group
    """
    taxa = Taxonomy.objects.filter(
        id__in=taxa_ids
    )
    try:
        taxon_group = TaxonGroup.objects.get(
            id=taxon_group_id
        )
    except TaxonGroup.DoesNotExist:
        return
    for taxonomy in taxa:
        taxon_group.taxonomies.add(taxonomy)
        BiologicalCollectionRecord.objects.filter(
            taxonomy=taxonomy
        ).update(module_group=taxon_group)


class TaxaUpdateMixin(UserPassesTestMixin, APIView):
    def test_func(self):
        return self.request.user.has_perm('bims.can_update_taxon_group')


class UpdateTaxonGroupOrder(TaxaUpdateMixin):
    """Api to update taxon groups order.
    Post data required:
    {
        'taxonGroups': [1,2] // List of taxon groups id sorted by their order
    }
    """
    def post(self, request, *args):
        taxon_groups_array = self.request.POST.get('taxonGroups', None)
        if not taxon_groups_array:
            raise Http404('Missing taxon groups')
        taxon_group_ids = json.loads(taxon_groups_array)
        update_taxon_group_orders(taxon_group_ids)
        return Response('Updated')


class RemoveTaxaFromTaxonGroup(TaxaUpdateMixin):
    """Api to remove taxa from taxon group.
    Post data required:
    {
        'taxaIds': [1,2], // List of taxa id
        'taxonGroupId': 1 // id of the taxon group
    }
    """
    def post(self, request, *args):
        taxa_ids = self.request.POST.get('taxaIds', None)
        taxon_group_id = self.request.POST.get('taxonGroupId', None)
        if not taxa_ids or not taxon_group_id:
            raise Http404('Missing required parameter')
        taxa_ids = json.loads(taxa_ids)
        taxon_group_id = int(taxon_group_id)
        remove_taxa_from_taxon_group(taxa_ids, taxon_group_id)
        return Response(
            {
                'taxonomy_count': TaxonGroup.objects.get(
                    id=taxon_group_id
                ).taxonomies.all().count()
            }
        )


class AddTaxaToTaxonGroup(TaxaUpdateMixin):
    """Api to add taxa to taxon group.
    Post data required:
    {
        'taxaIds': [1,2], // List of taxa id
        'taxonGroupId': 1 // id of the taxon group
    }
    """
    def post(self, request, *args):
        taxa_ids = self.request.POST.get('taxaIds', None)
        taxon_group_id = self.request.POST.get('taxonGroupId', None)
        if not taxa_ids or not taxon_group_id:
            raise Http404('Missing required parameter')
        taxa_ids = json.loads(taxa_ids)
        taxon_group_id = int(taxon_group_id)
        add_taxa_to_taxon_group(taxa_ids, taxon_group_id)
        return Response(
            {
                'taxonomy_count': TaxonGroup.objects.get(
                    id=taxon_group_id
                ).taxonomies.all().count()
            }
        )
