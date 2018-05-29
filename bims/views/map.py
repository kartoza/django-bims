# coding=utf-8
from django.views.generic import TemplateView
import os

try:
    from core.settings.secret import BING_MAP_KEY
except ImportError:
    BING_MAP_KEY = ''

try:
    GEOCONTEX_URL = os.environ['GEOCONTEXT_URL']
except KeyError:
    GEOCONTEX_URL = ''


class MapPageView(TemplateView):
    """Template view for map page"""
    template_name = 'map.html'

    def get_context_data(self, **kwargs):
        """Get the context data which is passed to a template.

        :param kwargs: Any arguments to pass to the superclass.
        :type kwargs: dict

        :returns: Context data which will be passed to the template.
        :rtype: dict
        """
        context = super(MapPageView, self).get_context_data(**kwargs)
        context['bing_map_key'] = BING_MAP_KEY
        context['geocontext_url'] = GEOCONTEX_URL
        return context
