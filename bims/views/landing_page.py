# coding=utf-8
from django.views.generic import TemplateView
try:
    from core.settings.secret import BING_MAP_KEY
except ImportError:
    BING_MAP_KEY = ''


class LandingPageView(TemplateView):
    """Template view for landing page"""
    template_name = 'map.html'

    def get_context_data(self, **kwargs):
        """Get the context data which is passed to a template.

        :param kwargs: Any arguments to pass to the superclass.
        :type kwargs: dict

        :returns: Context data which will be passed to the template.
        :rtype: dict
        """
        context = super(LandingPageView, self).get_context_data(**kwargs)
        context['bing_map_key'] = BING_MAP_KEY
        return context
