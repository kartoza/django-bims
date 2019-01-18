from django.views.generic import TemplateView
from django.shortcuts import get_object_or_404
from bims.models.location_site import LocationSite
from bims.views.prometheus_monitor import PrometheusCounter
from sass.models import SassTaxon


class FormView(PrometheusCounter, TemplateView):
    """Template view for landing page"""
    template_name = 'form_page.html'

    def get_context_data(self, **kwargs):
        context = super(FormView, self).get_context_data(**kwargs)
        sass_5_taxa = SassTaxon.objects.filter(
            taxon_sass_5__isnull=False
        ).order_by('display_order_sass_5')
        taxon_list = []
        for sass_5_taxon in sass_5_taxa:
            taxon_list.append({
                'name': sass_5_taxon.taxon_sass_5,
                'has_score': (
                    False if sass_5_taxon.sass_5_score is None else True
                ),
                'should_bold': (
                    sass_5_taxon.taxon_sass_5.split(' ')[0].isupper()
                )
            })
        context['taxon_list'] = taxon_list
        return context

    def get(self, request, *args, **kwargs):
        site_id = kwargs.get('site_id', None)
        site = get_object_or_404(
            LocationSite,
            pk=site_id
        )
        print(site)
        return super(FormView, self).get(request, *args, **kwargs)
