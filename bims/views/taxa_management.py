# coding=utf-8
"""Taxa management view
"""
import json

from django.contrib.sites.shortcuts import get_current_site
from django.http import Http404
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from bims.models.taxon_group import TaxonGroup
from bims.models.biological_collection_record import BiologicalCollectionRecord
from bims.enums.taxonomic_rank import TaxonomicRank
from bims.models.taxonomy import Taxonomy
from bims.models.endemism import Endemism
from bims.models.iucn_status import IUCNStatus
from bims.serializers.taxon_serializer import TaxonGroupSerializer


class TaxaManagementView(LoginRequiredMixin, TemplateView):
    template_name = 'taxa_management.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        site = get_current_site(self.request)
        taxa_groups_query = TaxonGroup.objects.filter(
            category='SPECIES_MODULE',
            parent__isnull=True,
            site=site).order_by('display_order')
        context['taxa_groups'] = TaxonGroupSerializer(
            taxa_groups_query, many=True).data
        context['taxa_groups_json'] = json.dumps(context['taxa_groups'])
        context['source_collections'] = list(
            BiologicalCollectionRecord.objects.values_list(
                'source_collection', flat=True).distinct()
        )
        context['taxon_rank'] = [
            rank.name for rank in TaxonomicRank
            if rank in (TaxonomicRank.GENUS, TaxonomicRank.SPECIES)
        ]
        context['all_ranks'] = [rank.name for rank in TaxonomicRank]
        context['all_origins'] = [
            {'value': origin[0], 'label': origin[1]} for origin in Taxonomy.CATEGORY_CHOICES]
        context['all_endemism'] = Endemism.objects.exclude(
            name='').values_list('name', flat=True).distinct()
        context['all_cons_status'] = [
            {'value': status[0], 'label': status[1]} for status in IUCNStatus.CATEGORY_CHOICES]
        context['is_expert'] = self.is_user_expert_for_taxon(
            self.request.GET.get('selected'))
        return context

    def is_user_expert_for_taxon(self, selected_taxon_id):
        if not selected_taxon_id:
            return False
        try:
            selected_taxon_group = TaxonGroup.objects.get(
                id=selected_taxon_id)
            return selected_taxon_group.experts.filter(
                id=self.request.user.id).exists()
        except TaxonGroup.DoesNotExist:
            raise Http404("Taxon Group does not exist")
