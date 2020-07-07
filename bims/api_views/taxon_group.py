import json
from django.contrib.auth.mixins import UserPassesTestMixin
from django.http import Http404, HttpResponseForbidden
from rest_framework.response import Response
from rest_framework.views import APIView
from bims.models import TaxonGroup


class UpdateTaxonGroupOrder(UserPassesTestMixin, APIView):
    """Add new taxon, then return the id of newly created taxon"""
    def test_func(self):
        return self.request.user.has_perm('bims.can_update_taxon_group')

    def post(self, request, *args):
        taxon_groups_array = self.request.POST.get('taxonGroups', None)
        if not taxon_groups_array:
            raise Http404('Missing taxon groups')
        taxon_groups_array = json.loads(taxon_groups_array)
        taxon_groups = TaxonGroup.objects.filter(
            id__in=taxon_groups_array
        )
        for taxon_group in taxon_groups:
            try:
                order = taxon_groups_array.index(taxon_group.id)
                taxon_group.display_order = order
                taxon_group.save()
            except ValueError:
                continue
        return Response('Updated')
