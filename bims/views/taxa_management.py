# coding=utf-8
"""Taxa management view
"""
from django.views.generic import TemplateView
from django.contrib.auth.mixins import UserPassesTestMixin, LoginRequiredMixin
from bims.models.taxon_group import TaxonGroup
from bims.models.biological_collection_record import BiologicalCollectionRecord
from bims.enums.taxonomic_rank import TaxonomicRank
from bims.models.taxonomy import Taxonomy
from bims.models.endemism import Endemism
from bims.models.iucn_status import IUCNStatus
from bims.serializers.taxon_serializer import TaxonGroupSerializer


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
        context['taxa_groups'] = TaxonGroupSerializer(
            TaxonGroup.objects.filter(
                category='SPECIES_MODULE'
            ).order_by('display_order'), many=True).data
        context['source_collections'] = list(
            BiologicalCollectionRecord.objects.all().values_list(
                'source_collection', flat=True
            ).distinct('source_collection')
        )
        context['taxon_rank'] = [
            TaxonomicRank.GENUS.name,
            TaxonomicRank.SPECIES.name
        ]
        context['all_ranks'] = [rank.name for rank in TaxonomicRank]
        context['all_origins'] = [
            {
                'value': origin[0], 'label': origin[1]
            } for origin in Taxonomy.CATEGORY_CHOICES
        ]
        context['all_endemism'] = list(dict.fromkeys((
            Endemism.objects.all().exclude(name='').values_list(
                'name', flat=True)
        )))
        context['all_cons_status'] = list(
            {
                'value': status[0], 'label': status[1]
            } for status in IUCNStatus.CATEGORY_CHOICES
        )
        return context
