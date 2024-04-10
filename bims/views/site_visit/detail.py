import threading
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator

from bims.models import WaterTemperature
from bims.models.location_site import LocationSite

from bims.models.biological_collection_record import BiologicalCollectionRecord
from django.contrib import messages
from django.views.generic import View
from django.contrib.auth.mixins import UserPassesTestMixin
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.views.generic.detail import DetailView

from bims.utils.search_process import clear_finished_search_process
from bims.views.site_visit.base import SiteVisitBaseView
from bims.models.survey import Survey
from bims.models.basemap_layer import BaseMapLayer
from bims.models.chemical_record import ChemicalRecord


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
    site_visit = None
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

    def dispatch(self, request, *args, **kwargs):
        return super(SiteVisitDeleteView, self).dispatch(request, *args, **kwargs)

    def run_in_background(self, site_visit_id: int):
        survey = Survey.objects.get(id=site_visit_id)
        surveys = Survey.objects.filter(site=survey.site)
        BiologicalCollectionRecord.objects.filter(survey=survey).delete()
        ChemicalRecord.objects.filter(survey=survey).delete()
        Survey.objects.filter(id=survey.id).delete()

        if len(surveys) == 1:
            location_site = LocationSite.objects.get(pk=survey.site.id)
            if not ChemicalRecord.objects.filter(
                location_site=location_site
            ).exists() and not WaterTemperature.objects.filter(
                location_site=location_site
            ).exists():
                LocationSite.objects.filter(
                    id=location_site.id
                ).delete()

        clear_finished_search_process()

    @method_decorator(login_required)
    def post(self, request, *args, **kwargs):
        site_visit = get_object_or_404(
            Survey,
            id=self.kwargs.get('sitevisitid', None)
        )
        self.site_visit = site_visit

        background_thread = threading.Thread(
            target=self.run_in_background,
            args=(self.site_visit.id,)
        )
        background_thread.start()

        messages.success(
            request,
            'Site visit successfully deleted!',
            extra_tags='delete_site_visit'
        )
        redirect_url = '/site-visit/list/'
        next_url = request.POST.get('next', None)
        if next_url:
            redirect_url = next_url

        return HttpResponseRedirect(redirect_url)
