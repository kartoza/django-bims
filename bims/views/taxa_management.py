# coding=utf-8
"""Taxa management view
"""
from django.views.generic import TemplateView
from django.contrib.auth.mixins import UserPassesTestMixin, LoginRequiredMixin
from bims.models.taxon_group import TaxonGroup
from bims.enums.taxonomic_rank import TaxonomicRank


class TaxaManagementView(
    UserPassesTestMixin,
    LoginRequiredMixin,
    TemplateView):

    template_name = 'taxa_management.html'

    def test_func(self):
        return self.request.user.has_perm('bims.can_upload_taxa')

    def get_context_data(self, **kwargs):
        context = super(TaxaManagementView, self).get_context_data(
            **kwargs
        )
        context['taxa_groups'] = TaxonGroup.objects.filter(
            category='SPECIES_MODULE'
        ).order_by('display_order')
        context['taxon_rank'] = [
            TaxonomicRank.GENUS.name,
            TaxonomicRank.SPECIES.name
        ]
        return context
