# coding=utf-8
"""Dashboard management view
"""
from django.views.generic import TemplateView
from django.contrib.auth.mixins import UserPassesTestMixin, LoginRequiredMixin
from django.http import HttpResponseRedirect
from bims.models.taxon_group import TaxonGroup
from bims.models.dashboard_configuration import DashboardConfiguration


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
        context['module_groups'] = TaxonGroup.objects.filter(
            category='SPECIES_MODULE'
        ).order_by('display_order')
        if self.request.GET.get('module_group'):
            context['module_group'] = TaxonGroup.objects.get(
                id=self.request.GET.get('module_group')
            )
        else:
            context['module_group'] = context['module_groups'][0]
        try:
            context['dashboard_configuration'] = (
                DashboardConfiguration.objects.get(
                    module_group=context['module_group']
                )
            )
        except DashboardConfiguration.DoesNotExist:
            pass
        return context

    def post(self, request, *args, **kwargs):
        dashboard_configuration, _ = (
            DashboardConfiguration.objects.get_or_create(
                module_group_id=request.POST.get('module_group', None)
            )
        )
        dashboard_configuration.additional_data = (
            request.POST.get('dashboard_configuration', '{}')
        )
        dashboard_configuration.save()
        return HttpResponseRedirect(
            request.path_info + '?module_group=' + request.POST.get(
                'module_group', None)
        )
