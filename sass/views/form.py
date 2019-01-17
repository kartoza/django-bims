from django.views.generic import TemplateView
from bims.views.prometheus_monitor import PrometheusCounter


class FormView(PrometheusCounter, TemplateView):
    """Template view for landing page"""
    template_name = 'form_page.html'
