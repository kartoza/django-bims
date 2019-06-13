from django.views.generic import TemplateView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator

from bims.utils.get_key import get_key


class LocationSiteFormView(TemplateView):
    template_name = 'location_site_form_view.html'

    def get_context_data(self, **kwargs):
        context = super(LocationSiteFormView, self).get_context_data(**kwargs)
        context['geoserver_public_location'] = get_key(
            'GEOSERVER_PUBLIC_LOCATION')
        return context

    @method_decorator(login_required)
    def get(self, request, *args, **kwargs):
        return super(LocationSiteFormView, self).get(request, *args, **kwargs)
