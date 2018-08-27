# coding=utf-8
import os
from django.db.models import Max, Min
from django.views.generic import TemplateView
from bims.utils.get_key import get_key
from bims.models.biological_collection_record import (
    BiologicalCollectionRecord
)
from bims.models.profile import Profile as BimsProfile
from django.contrib.flatpages.models import FlatPage


class MapPageView(TemplateView):
    """Template view for map page"""

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

        categories = BiologicalCollectionRecord.CATEGORY_CHOICES
        context['collection_category'] = [list(x) for x in categories]

        bio_childrens = BiologicalCollectionRecord.get_children_model()

        # add additional module
        context['biological_modules'] = {
            bio._meta.app_label: str(bio._meta.label) for bio in bio_childrens
        }
        # add base module
        context['biological_modules']['base'] = 'base'

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

        if self.request.user:
            try:
                user_profile = BimsProfile.objects.get(user=self.request.user)
                context['hide_bims_info'] = user_profile.hide_bims_info
            except (BimsProfile.DoesNotExist, TypeError):
                pass

        try:
            context['flatpage'] = FlatPage.objects.get(title__icontains='info')
        except FlatPage.DoesNotExist:
            pass

        return context
