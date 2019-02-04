from django.views.generic import TemplateView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.shortcuts import get_object_or_404
from bims.models import LocationSite


class FishFormView(TemplateView):
    """View for fish form"""
    template_name = 'fish_form_page.html'
    location_site = None

    def get_context_data(self, **kwargs):
        context = super(FishFormView, self).get_context_data(**kwargs)
        context['location_site_name']  = self.location_site.name
        context['location_site_lat'] = self.location_site.get_centroid().y
        context['location_site_long'] = self.location_site.get_centroid().x
        return context

    @method_decorator(login_required)
    def get(self, request, *args, **kwargs):
        site_id = request.GET.get('siteId', None)
        if site_id:
            self.location_site =  get_object_or_404(
                LocationSite,
                pk=site_id
            )

        return super(FishFormView, self).get(request, *args, **kwargs)
