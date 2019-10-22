# coding=utf-8
from django.views.generic import TemplateView
from bims.models.carousel_header import CarouselHeader
from bims.views.prometheus_monitor import PrometheusCounter
from bims.utils.summary import get_landing_page_summary


class LandingPageView(PrometheusCounter, TemplateView):
    """Template view for landing page"""
    template_name = 'landing_page.html'

    def get_context_data(self, **kwargs):
        """Get the context data which is passed to a template.

        :param kwargs: Any arguments to pass to the superclass.
        :type kwargs: dict

        :returns: Context data which will be passed to the template.
        :rtype: dict
        """
        context = super(LandingPageView, self).get_context_data(**kwargs)
        self.increase_landing_page_view()
        carousel_headers = CarouselHeader.objects.all()
        context['headers'] = []
        context['summaries'] = []
        for header in carousel_headers:
            context['headers'].append({
                'file': header.banner,
                'description': header.description
            })
        return context
