# coding=utf-8
import os
from distutils import util as distutil
from django.db.models import Max, Min
from django.views.generic import TemplateView
from django.contrib.flatpages.models import FlatPage
from bims.utils.get_key import get_key
from bims.models.biological_collection_record import (
    BiologicalCollectionRecord
)
from bims.models.profile import Profile as BimsProfile
from bims.models.iucn_status import IUCNStatus
from bims.permissions.api_permission import user_has_permission_to_validate


class MapPageView(TemplateView):
    """Template view for map page"""
    COLLECTOR_FILTER = 'COLLECTOR_FILTER'

    # change template based on map
    try:
        app_name = os.environ['APP_NAME']
    except KeyError:
        app_name = 'bims'

    template_name = 'map_page/%s.html' % app_name

    def get_context_data(self, **kwargs):
        """Get the context data which is passed to a template.

        :param kwargs: Any arguments to pass to the superclass.
        :type kwargs: dict

        :returns: Context data which will be passed to the template.
        :rtype: dict
        """
        context = super(MapPageView, self).get_context_data(**kwargs)
        context['bing_map_key'] = get_key('BING_MAP_KEY')
        context['map_tiler_key'] = get_key('MAP_TILER_KEY')
        context['geocontext_url'] = get_key('GEOCONTEXT_URL')
        context['geocontext_collection_key'] = get_key(
            'GEOCONTEXT_COLLECTION_KEY')
        context['center_point_map'] = get_key('CENTER_POINT_MAP')
        context['can_validate'] = user_has_permission_to_validate(
                self.request.user)

        categories = BiologicalCollectionRecord.CATEGORY_CHOICES
        context['collection_category'] = [list(x) for x in categories]

        # Additional filters
        context['use_ecological_condition'] = bool(
                get_key('ECOLOGICAL_CONDITION_FILTER'))
        context['use_conservation_status'] = bool(
                get_key('CONSERVATION_STATUS_FILTER'))

        # Search panel titles
        date_title = get_key('DATE_TITLE')
        if not date_title:
            date_title = 'DATE'
        context['date_title'] = date_title

        spatial_scale = get_key('SPATIAL_SCALE_TITLE')
        if not spatial_scale:
            spatial_scale = 'ADMINISTRATIVE AREA'
        context['spatial_scale_title'] = spatial_scale

        # get date filter
        context['date_filter'] = {'min': '1900', 'max': '2008'}
        date_min = BiologicalCollectionRecord.objects.all(
        ).aggregate(min=Min('collection_date'))['min']
        date_max = BiologicalCollectionRecord.objects.all(
        ).aggregate(max=Max('collection_date'))['max']
        if date_min:
            context['date_filter']['min'] = date_min.year
        if date_max:
            context['date_filter']['max'] = date_max.year

        # Is it necessary to use collector filter, default true
        collector_filter = get_key(self.COLLECTOR_FILTER)
        if not collector_filter:
            context[self.COLLECTOR_FILTER] = True
        else:
            context[self.COLLECTOR_FILTER] = distutil.strtobool(
                    collector_filter)

        if self.request.user:
            try:
                user_profile = BimsProfile.objects.get(user=self.request.user)
                context['hide_bims_info'] = user_profile.hide_bims_info
            except (BimsProfile.DoesNotExist, TypeError):
                pass

        # Get all the iucn conservation status
        if context['use_conservation_status']:
            iucn_statuses = IUCNStatus.objects.all().distinct('category')
            conservation_status_data = []
            categories = dict(IUCNStatus.CATEGORY_CHOICES)
            for iucn_status in iucn_statuses:
                conservation_status_data.append({
                    'status': str(iucn_status.category),
                    'name': categories[iucn_status.category]
                })
            context['conservation_status_data'] = conservation_status_data

        try:
            context['flatpage'] = FlatPage.objects.get(title__icontains='info')
        except FlatPage.DoesNotExist:
            pass

        return context
