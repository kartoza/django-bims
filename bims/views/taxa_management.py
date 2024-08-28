# coding=utf-8
"""Taxa management view
"""
import json
from urllib.parse import urlencode

from django.contrib.sites.shortcuts import get_current_site
from django.http import Http404, HttpResponseRedirect
from django.urls import reverse
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin

from bims.cache import get_cache, set_cache
from bims.models.taxon_group import TaxonGroup, TAXON_GROUP_CACHE
from bims.models.biological_collection_record import BiologicalCollectionRecord
from bims.enums.taxonomic_rank import TaxonomicRank
from bims.models.taxonomy import Taxonomy
from bims.models.endemism import Endemism
from bims.models.iucn_status import IUCNStatus
from bims.serializers.taxon_serializer import TaxonGroupSerializer


class TaxaManagementView(LoginRequiredMixin, TemplateView):
    template_name = 'taxa_management.html'

    def remove_selected_param_from_url(self, request):
        query_params = request.GET.copy()
        query_params.pop('selected', None)
        base_url = reverse('taxa-management')
        new_url = f"{base_url}?{urlencode(query_params)}"
        return HttpResponseRedirect(new_url)

    def dispatch(self, request, *args, **kwargs):
        selected = request.GET.get('selected')
        if selected:
            try:
                TaxonGroup.objects.get(id=selected)
            except TaxonGroup.DoesNotExist:
                return self.remove_selected_param_from_url(request)
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        site = get_current_site(self.request)
        selected = self.request.GET.get('selected')
        taxon_group_cache = get_cache(TAXON_GROUP_CACHE)
        if taxon_group_cache:
            context['taxa_groups'] = taxon_group_cache
        else:
            taxa_groups_query = TaxonGroup.objects.filter(
                category='SPECIES_MODULE',
                parent__isnull=True
            ).order_by('display_order')
            context['taxa_groups'] = TaxonGroupSerializer(
                taxa_groups_query, many=True).data
            set_cache(TAXON_GROUP_CACHE, context['taxa_groups'])
        context['selected_taxon_group'] = None
        if selected:
            try:
                context['selected_taxon_group'] = TaxonGroup.objects.get(
                    id=selected
                )
            except TaxonGroup.DoesNotExist:
                pass

        if not context['selected_taxon_group']:
            context['selected_taxon_group'] = TaxonGroup.objects.filter(
                category='SPECIES_MODULE',
            ).first()

        context['taxa_groups_json'] = json.dumps(context['taxa_groups'])
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
        all_taxonomic_status = (
            Taxonomy.objects.all().values_list('taxonomic_status', flat=True).distinct('taxonomic_status')
        )
        context['all_taxonomic_status'] = []
        for taxonomic_status in all_taxonomic_status:
            if taxonomic_status and taxonomic_status.upper() not in context['all_taxonomic_status']:
                context['all_taxonomic_status'].append(taxonomic_status.upper())
        context['is_expert'] = self.request.user.is_superuser or self.is_user_expert_for_taxon(
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
