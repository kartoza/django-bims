from dateutil.parser import parse
from django.views.generic import TemplateView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.utils import timezone
from django.shortcuts import redirect
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.contrib.auth.mixins import UserPassesTestMixin
from geonode.people.models import Profile
from bims.models.location_site import LocationSite
from bims.models.biotope import Biotope
from bims.models.data_source import DataSource
from sass.models import (
    SiteVisit,
    SassTaxon,
    SiteVisitBiotopeTaxon,
    SiteVisitTaxon,
    TaxonAbundance,
    Rate,
    SassBiotopeFraction
)

BIOTOPE_STONES = 'SIC/SOOC'
BIOTOPE_VEGETATION = 'MV/AQV'
BIOTOPE_GSM = 'G/S/M'

# Biotope Sampled Sheet
BSS_STONES_IN_CURRENT = 'Stones in current (SIC)'
BSS_STONES_OUT_OF_CURRENT = 'Stones out of current (SOOC)'


class SassFormView(UserPassesTestMixin, TemplateView):
    """Template view for landing page"""
    template_name = 'form_page.html'
    post_dictionary = {}
    site_visit = SiteVisit.objects.none()
    sass_version = 5
    site_code = ''

    def test_func(self):
        if self.request.user.is_superuser:
            return True
        sass_id = self.kwargs.get('sass_id', None)
        if not sass_id:
            return True
        return SiteVisit.objects.filter(
            id=sass_id,
            owner=self.request.user).exists()

    def get_biotope_fractions(self, post_dictionary):
        # Get biotope fractions
        biotope_fractions = []
        biotope_list = dict(
            Biotope.objects.filter(biotope_form=1).values_list(
                'name', 'id'
            ))
        for biotope_key, biotope_id in biotope_list.iteritems():
            biotope_value = post_dictionary.get(biotope_key, None)
            try:
                if biotope_value:
                    rate = Rate.objects.get(
                        rate=biotope_value,
                        group=2
                    )
                else:
                    # Empty rate
                    rate = Rate.objects.get(
                        rate=-1,
                        group=2
                    )
                biotope_fraction = SassBiotopeFraction.objects.get(
                    rate=rate,
                    sass_biotope_id=biotope_id
                )
                biotope_fractions.append(biotope_fraction)
            except (
                Rate.MultipleObjectsReturned,
                SassBiotopeFraction.MultipleObjectsReturned):
                continue
        return biotope_fractions

    def update_site_visit_biotope_taxon(
        self,
        site_visit,
        post_dictionary,
        date):
        biotope_labels = {
            'S': 'SIC/SOOC',
            'Veg': 'MV/AQV',
            'GSM': 'G/S/M'
        }
        for post_key, abundance in post_dictionary.iteritems():
            if 'taxon_list' not in post_key:
                continue
            taxon_id = post_key.split('-')[1]
            sass_taxon = SassTaxon.objects.get(id=taxon_id)
            biotope_identifier = post_key.split('-')[2]
            taxon_abundance = TaxonAbundance.objects.get(
                abc=abundance
            )

            # S, Veg, GSM
            if biotope_identifier in biotope_labels:
                biotope_name = biotope_labels[biotope_identifier]
                biotope = Biotope.objects.get(
                    name=biotope_name
                )
                site_visit_biotope_taxon, status = (
                    SiteVisitBiotopeTaxon.objects.get_or_create(
                        site_visit=site_visit,
                        sass_taxon=sass_taxon,
                        taxon=sass_taxon.taxon,
                        biotope=biotope,
                    )
                )
                site_visit_biotope_taxon.taxon_abundance = taxon_abundance
                site_visit_biotope_taxon.date = date
                site_visit_biotope_taxon.save()

            # Total Rating
            site_visit_taxon, created = (
                SiteVisitTaxon.objects.get_or_create(
                    site=site_visit.location_site,
                    site_visit=site_visit,
                    sass_taxon=sass_taxon,
                    taxonomy=sass_taxon.taxon,
                    original_species_name=sass_taxon.taxon.canonical_name,
                    collector=self.request.user.username,
                    notes='from sass',
                )
            )
            site_visit_taxon.owner = self.request.user
            site_visit_taxon.collection_date = date
            site_visit_taxon.taxon_abundance = taxon_abundance
            site_visit_taxon.save()

    @method_decorator(login_required)
    def post(self, request, *args, **kwargs):
        site_id = kwargs.get('site_id', None)
        sass_id = kwargs.get('sass_id', None)

        # Assessor
        assessor_id = request.POST.get('assessor', None)
        assessor = None
        if assessor_id:
            try:
                assessor = Profile.objects.get(id=int(assessor_id))
            except Profile.DoesNotExist:
                pass

        # Date
        date_string = request.POST.get('date', None)
        date = parse(date_string) if date_string else None

        # Data source
        data_source = None
        data_source_name = request.POST.get('data-source-name', None)
        data_source_id = request.POST.get('data-source-id', None)
        if data_source_name and data_source_id:
            try:
                data_source = DataSource.objects.get(
                    id=data_source_id,
                    name=data_source_name
                )
            except DataSource.DoesNotExist:
                data_source = DataSource.objects.create(
                    name=data_source_name
                )

        # Time
        time_string = request.POST.get('time', None)
        datetime = None
        if time_string:
            try:
                hour, minute = time_string.split(':')
                datetime = date if date else timezone.now()
                datetime = datetime.replace(hour=int(hour), minute=int(minute))
            except ValueError:
                pass

        if not sass_id and site_id:
            site_visit = SiteVisit.objects.create(
                owner=self.request.user,
                location_site_id=site_id
            )
        else:
            site_visit = SiteVisit.objects.get(
                pk=sass_id
            )

        biotope_fractions = self.get_biotope_fractions(self.request.POST)

        site_visit.sass_biotope_fraction.add(*biotope_fractions)
        site_visit.site_visit_date = date
        site_visit.time = datetime
        site_visit.assessor = assessor
        site_visit.sass_version = self.sass_version
        site_visit.data_source = data_source
        site_visit.comments_or_observations = request.POST.get(
            'notes', None
        )
        site_visit.other_biota = request.POST.get(
            'other-biota', None
        )
        site_visit.save()
        self.update_site_visit_biotope_taxon(
            site_visit,
            self.request.POST,
            date)

        if site_id:
            return redirect(
                reverse('sass-form-page', kwargs={'site_id': site_id}))
        else:
            return redirect(
                reverse('sass-update-page', kwargs={'sass_id': sass_id})
            )

    def get_biotope_form_data(self):
        biotope_form_list = []
        biotope_fractions = []
        if self.site_visit:
            biotope_fractions = dict(
                self.site_visit.sass_biotope_fraction.all().values_list(
                    'sass_biotope__name', 'rate__rate'
                )
            )
        biotope_list = Biotope.objects.filter(biotope_form=1).order_by(
            'display_order')
        for biotope_data in biotope_list:
            biotope_rate = -1
            if biotope_data.name in biotope_fractions:
                biotope_rate = biotope_fractions[biotope_data.name]
            biotope_form_list.append({
                'name': biotope_data.name,
                'rate': biotope_rate
            })
        return biotope_form_list

    def get_taxon_list(self):
        taxon_list_form = []
        taxon_filters = dict()
        biotope_taxon_list = None
        site_visit_taxon_list = None
        taxon_filters[
            ('display_order_sass_%s__isnull' % self.sass_version)] = False
        sass_taxon_list = SassTaxon.objects.filter(**taxon_filters).order_by(
            'display_order_sass_%s' % self.sass_version
        )
        if self.site_visit:
            biotope_taxon_list = (
                self.site_visit.sitevisitbiotopetaxon_set.all()
            )
            site_visit_taxon_list = dict((
                self.site_visit.sitevisittaxon_set.all()
            ).values_list('sass_taxon__id', 'taxon_abundance__abc'))

        for sass_taxon in sass_taxon_list:
            if self.sass_version == 5:
                sass_taxon_score = sass_taxon.sass_5_score
            else:
                sass_taxon_score = sass_taxon.score

            if sass_taxon.taxon_sass_4:
                sass_taxon_name = sass_taxon.taxon_sass_4
            else:
                sass_taxon_name = sass_taxon.taxon_sass_5

            taxon_dict = {
                'name': sass_taxon_name.upper(),
                'id': sass_taxon.id,
                'score': sass_taxon_score,
                's_value': None,
                'veg_value': None,
                'gsm_value': None,
                'tot_value': None,
            }

            if not self.site_visit:
                taxon_list_form.append(taxon_dict)
                continue

            sass_taxon_biotope = dict(biotope_taxon_list.filter(
                sass_taxon=sass_taxon).values_list(
                'biotope__name',
                'taxon_abundance__abc'))

            if sass_taxon_biotope:
                if BIOTOPE_STONES in sass_taxon_biotope:
                    taxon_dict['s_value'] = (
                        sass_taxon_biotope[BIOTOPE_STONES]
                    )
                if BIOTOPE_VEGETATION in sass_taxon_biotope:
                    taxon_dict['veg_value'] = (
                        sass_taxon_biotope[BIOTOPE_VEGETATION]
                    )
                if BIOTOPE_GSM in sass_taxon_biotope:
                    taxon_dict['gsm_value'] = (
                        sass_taxon_biotope[BIOTOPE_GSM]
                    )
            if sass_taxon.id in site_visit_taxon_list:
                taxon_dict['tot_value'] = (
                    site_visit_taxon_list[sass_taxon.id]
                )

            taxon_list_form.append(taxon_dict)
        return taxon_list_form

    def get_context_data(self, **kwargs):
        context = super(SassFormView, self).get_context_data(**kwargs)

        if self.site_visit:
            context['is_update'] = True
            context['assessor'] = self.site_visit.assessor
            context['date'] = self.site_visit.site_visit_date
            context['time'] = self.site_visit.time
            if self.site_visit.comments_or_observations:
                context['comments'] = self.site_visit.comments_or_observations
            if self.site_visit.other_biota:
                context['other_biota'] = self.site_visit.other_biota
            context['data_source'] = self.site_visit.data_source

        context['biotope_form_list'] = self.get_biotope_form_data()
        context['taxon_list'] = self.get_taxon_list()
        context['site_code'] = self.site_code

        return context

    @method_decorator(login_required)
    def get(self, request, *args, **kwargs):
        site_id = kwargs.get('site_id')
        sass_id = kwargs.get('sass_id')
        sass_version_param = kwargs.get('sass_version')
        if sass_version_param:
            self.sass_version = int(sass_version_param)

        self.post_dictionary = {}
        if site_id:
            location_site = get_object_or_404(
                LocationSite,
                pk=site_id
            )
            self.site_code = location_site.site_code
            if not self.site_code:
                self.site_code = location_site.name
            self.sass_version = request.GET.get('sass_version', 5)
        else:
            self.site_visit = get_object_or_404(
                SiteVisit,
                pk=sass_id
            )
            self.site_code = self.site_visit.location_site.site_code
            if not self.site_code:
                self.site_code = self.site_visit.location_site.name
            if self.site_visit.sass_version:
                self.sass_version = self.site_visit.sass_version
        return super(SassFormView, self).get(request, *args, **kwargs)
