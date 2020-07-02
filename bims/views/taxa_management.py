# coding=utf-8
"""Taxa management view
"""
from datetime import datetime
from rest_framework.views import APIView
from rest_framework.response import Response
from django.views.generic import TemplateView
from django.http import HttpResponseRedirect, Http404
from django.contrib.auth.mixins import UserPassesTestMixin, LoginRequiredMixin
from bims.models.taxa_upload_session import TaxaUploadSession
from bims.models.taxon_group import TaxonGroup
from bims.tasks.taxa_upload import taxa_upload


class TaxaManagementView(UserPassesTestMixin, LoginRequiredMixin, TemplateView):

    template_name = 'taxa_management.html'

    def test_func(self):
        return self.request.user.has_perm('bims.can_upload_taxa')

    def get_context_data(self, **kwargs):
        context = super(TaxaManagementView, self).get_context_data(
            **kwargs
        )
        context['taxa_groups'] =  TaxonGroup.objects.filter(
            category='SPECIES_MODULE'
        ).order_by('display_order')
        return context
