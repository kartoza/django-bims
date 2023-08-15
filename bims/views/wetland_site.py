from bims.views.location_site import LocationSiteFormView


class WetlandSiteFormView(LocationSiteFormView):
    template_name = 'wetland_site_form.html'
    success_message = 'New site has been successfully added'
    location_site = None
