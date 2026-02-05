# coding=utf-8
from braces.views import LoginRequiredMixin
from django.views.generic import TemplateView


class SpatialDashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'spatial_dashboard.html'
