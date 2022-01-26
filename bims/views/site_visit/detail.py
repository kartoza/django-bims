from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt

from bims.models.location_site import LocationSite

from bims.models.biological_collection_record import BiologicalCollectionRecord
from django.contrib import messages
from django.views.generic import View
from django.contrib.auth.mixins import UserPassesTestMixin
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.views.generic.detail import DetailView
from bims.views.site_visit.base import SiteVisitBaseView
from bims.models.survey import Survey
from bims.models.basemap_layer import BaseMapLayer


class SiteVisitDetailView(SiteVisitBaseView, DetailView):
    template_name = 'site_visit/site_visit_detail.html'
    model = Survey
    pk_url_kwarg = 'sitevisitid'

    def get_context_data(self, **kwargs):
        context = super(SiteVisitDetailView, self).get_context_data(**kwargs)
        context['detail'] = True
        try:
            context['bing_key'] = (
                BaseMapLayer.objects.get(source_type='bing').key
            )
        except BaseMapLayer.DoesNotExist:
            context['bing_key'] = ''
        return context


class SiteVisitDeleteView(UserPassesTestMixin, View):
    def test_func(self):
        if self.request.user.is_anonymous:
            return False
        if self.request.user.is_superuser:
            return True
        site_visit_id = self.kwargs.get('sitevisitid', None)
        if not site_visit_id:
            return True
        return Survey.objects.filter(
                id=site_visit_id, ).exists()

    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        return super(SiteVisitDeleteView, self).dispatch(request, *args, **kwargs)

    @method_decorator(login_required)
    def post(self, request, *args, **kwargs):
        site_visit = get_object_or_404(
            Survey,
            id=self.kwargs.get('sitevisitid', None)
        )
        surveys = Survey.objects.filter(site=site_visit.site)
        if len(surveys) == 1:
            LocationSite.objects.get(pk=site_visit.site.id).delete()
        BiologicalCollectionRecord.objects.filter(survey=site_visit).delete()
        Survey.objects.filter(id=site_visit.id).delete()
        messages.success(
            request,
            'Site visit successfully deleted!',
            extra_tags='delete_site_visit'
        )
        redirect_url = '/site-visit/list/'

        return HttpResponseRedirect(redirect_url)
