from django.views.generic import TemplateView
from guardian.mixins import LoginRequiredMixin


class WetlandSiteFormView(LoginRequiredMixin, TemplateView):
    template_name = 'wetland_site_form.html'
    success_message = 'New site has been successfully added'
    location_site = None
