# coding=utf-8
"""Dashboard management view
"""
from django.views.generic import TemplateView
from django.contrib.auth.mixins import UserPassesTestMixin, LoginRequiredMixin
from bims.models.taxon_group import TaxonGroup


class DashboardManagementView(
    UserPassesTestMixin,
    LoginRequiredMixin,
    TemplateView):

    template_name = 'dashboard_management.html'

    def test_func(self):
        return self.request.user.has_perm('bims.can_upload_taxa')

    def get_context_data(self, **kwargs):
        context = super(DashboardManagementView, self).get_context_data(
            **kwargs
        )
        return context
