import json
from django.contrib.auth.mixins import UserPassesTestMixin
from django.http import Http404
from rest_framework.response import Response
from rest_framework.views import APIView
from bims.models import TaxonGroup


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


class UpdateTaxonGroupOrder(UserPassesTestMixin, APIView):
    """Api to update taxon groups order.
    Post data required:
    {
        'taxonGroups': [1,2] // List of taxon groups id sorted by their order
    }
    """

    def test_func(self):
        return self.request.user.has_perm('bims.can_update_taxon_group')

    def post(self, request, *args):
        taxon_groups_array = self.request.POST.get('taxonGroups', None)
        if not taxon_groups_array:
            raise Http404('Missing taxon groups')
        taxon_group_ids = json.loads(taxon_groups_array)
        update_taxon_group_orders(taxon_group_ids)
        return Response('Updated')
