import json

from django.http import HttpResponse

from bims.models.location_context import LocationContext
from django.shortcuts import get_object_or_404

from bims.models.location_site import LocationSite
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView
from bims.models.basemap_layer import BaseMapLayer


class PesticideDashboardView(TemplateView):
    """
    A Django view that displays information about the pesticide risks
    for a specific location site. The view requires the user to be logged
    in to access the data.
    """
    template_name = 'pesticide_dashboard.html'
    location_site = None
    location_context = None

    @method_decorator(login_required)
    def get(self, request, site_id) -> HttpResponse:
        """
        Retrieve and display the pesticide risk information for the
        specified location site.

        Args:
            request (HttpRequest): The request object.
            site_id (int): The primary key of the location site.

        Returns:
            HttpResponse: The response object.
        """
        self.location_site = get_object_or_404(
            LocationSite,
            pk=site_id
        )
        self.location_context = LocationContext.objects.filter(
            site=self.location_site
        )

        return super(
            PesticideDashboardView, self).get(request, site_id)

    def get_context_data(self, **kwargs) -> dict:
        """
        Retrieve context data for the view, including location site
        and pesticide risk information.

        Args:
            **kwargs: Additional keyword arguments.

        Returns:
            dict: The context data for the view.
        """
        context = super(
            PesticideDashboardView, self).get_context_data(**kwargs)
        if not self.location_site:
            return context
        context['location_site'] = self.location_site
        try:
            context['bing_key'] = BaseMapLayer.objects.get(
                source_type='bing').key
        except BaseMapLayer.DoesNotExist:
            context['bing_key'] = ''

        # pesticide_risk = {"mv_algae_risk": "Very Low",
        # "mv_fish_risk": "Very Low", "mv_invert_risk": "Very Low"};
        context['pesticide_risk'] = (
            json.dumps(self.location_context.values_from_group(
                'pesticide_risk'
            ))
        )
        site_description = self.location_site.site_description
        if not site_description:
            site_description = self.location_site.name
        context['site_description'] = site_description
        try:
            context['river'] = self.location_site.river.name
        except AttributeError:
            context['river'] = '-'
        context['river_catchments'] = json.dumps(
            self.location_context.values_from_group(
                'river_catchment_areas_group'
            ))
        context['wma'] = (
            json.dumps(self.location_context.values_from_group(
                'water_management_area'
            ))
        )
        context['geomorphological_group'] = (
            json.dumps(self.location_context.values_from_group(
                'geomorphological_group'
            ))
        )
        context['river_ecoregion_group'] = (
            json.dumps(self.location_context.values_from_group(
                'river_ecoregion_group'
            ))
        )
        context['freshwater_ecoregion_of_the_world'] = (
            json.dumps(self.location_context.values_from_group(
                'freshwater_ecoregion_of_the_world'
            ))
        )
        context['political_boundary'] = (
            json.dumps(self.location_context.values_from_group(
                'province'
            ))
        )
        refined_geomorphological = '-'
        if self.location_site.refined_geomorphological:
            refined_geomorphological = (
                self.location_site.refined_geomorphological
            )
        context['refined_geomorphological'] = refined_geomorphological

        return context
