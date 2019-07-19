from dateutil.parser import parse
from django.db.models import Case, When, F, Q, signals
from django.views.generic import TemplateView, View
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.utils import timezone
from django.shortcuts import redirect
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib.sites.models import Site
from django.template.loader import render_to_string
from django.core.mail import EmailMultiAlternatives
from django.contrib.auth.mixins import UserPassesTestMixin
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings

from geonode.people.models import Profile
from bims.models.location_site import (
    LocationSite,
    location_site_post_save_handler
)
from bims.models.taxonomy import Taxonomy
from bims.models.biotope import Biotope
from bims.models.data_source import DataSource
from bims.models.taxon_group import TaxonGroup
from sass.models import (
    SiteVisit,
    SassTaxon,
    SiteVisitBiotopeTaxon,
    SiteVisitTaxon,
    TaxonAbundance,
    Rate,
    SassBiotopeFraction
)
from bims.utils.search_process import clear_finished_search_process

from bims.enums import TaxonomicGroupCategory

BIOTOPE_STONES = 'SIC/SOOC'
BIOTOPE_VEGETATION = 'MV/AQV'
BIOTOPE_GSM = 'G/S/M'

# Biotope Sampled Sheet
BSS_STONES_IN_CURRENT = 'Stones in current (SIC)'
BSS_STONES_OUT_OF_CURRENT = 'Stones out of current (SOOC)'


class SassFormView(UserPassesTestMixin, TemplateView):
    """Template view for Sass Form"""
    template_name = 'form_page.html'
    post_dictionary = {}
    site_visit = SiteVisit.objects.none()
    sass_version = 5
    site_code = ''
    read_only = False
    source_collection = None

    def __init__(self, *args, **kwargs):
        super(SassFormView, self).__init__(*args, **kwargs)
        taxon_groups = TaxonGroup.objects.filter(
            name__icontains='Inverterbrates'
        )
        if taxon_groups.exists():
            self.source_collection = taxon_groups[0].source_collection

    def test_func(self):
        if self.request.user.is_anonymous:
            return False
        if self.request.user.is_superuser:
            return True
        sass_id = self.kwargs.get('sass_id', None)
        if not sass_id:
            return True
        return SiteVisit.objects.filter(
            Q(owner=self.request.user) | Q(assessor=self.request.user),
            id=sass_id,).exists()

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
                    rate = Rate.objects.filter(
                        rate=biotope_value,
                        group=2
                    ).exclude(description__icontains='not rated')
                else:
                    # Empty rate
                    rate = Rate.objects.filter(
                        description__icontains='not rated',
                        group=2
                    )
                if rate.exists():
                    rate = rate[0]
                else:
                    rate = Rate.objects.none()
                biotope_fraction, created = (
                    SassBiotopeFraction.objects.get_or_create(
                        rate=rate,
                        sass_biotope_id=biotope_id
                    )
                )
                biotope_fractions.append(biotope_fraction)
            except (
                Rate.MultipleObjectsReturned,
                SassBiotopeFraction.MultipleObjectsReturned,
                SassBiotopeFraction.DoesNotExist):
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
        updated_site_visit_taxon = []
        updated_site_visit_biotope_taxon = []
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
                updated_site_visit_biotope_taxon.append(
                    site_visit_biotope_taxon.id
                )
                site_visit_biotope_taxon.taxon_abundance = taxon_abundance
                site_visit_biotope_taxon.date = date
                site_visit_biotope_taxon.save()

            # Total Rating
            if 'TOT' == biotope_identifier:
                try:
                    site_visit_taxon, created = (
                        SiteVisitTaxon.objects.get_or_create(
                            site=site_visit.location_site,
                            site_visit=site_visit,
                            sass_taxon=sass_taxon,
                            taxonomy=sass_taxon.taxon,
                            original_species_name=
                            sass_taxon.taxon.canonical_name,
                            validated=True,
                            source_collection=self.source_collection
                        )
                    )
                except SiteVisitTaxon.MultipleObjectsReturned:
                    site_visit_taxa = SiteVisitTaxon.objects.filter(
                        site=site_visit.location_site,
                        site_visit=site_visit,
                        sass_taxon=sass_taxon,
                        taxonomy=sass_taxon.taxon,
                        original_species_name=sass_taxon.taxon.canonical_name,
                    )
                    site_visit_taxa.update(
                        source_collection=self.source_collection
                    )
                    site_visit_taxon = site_visit_taxa[0]
                    created = False
                updated_site_visit_taxon.append(
                    site_visit_taxon.id
                )
                site_visit_taxon.notes = 'from sass'
                site_visit_taxon.collection_date = date
                site_visit_taxon.taxon_abundance = taxon_abundance

                if created:
                    site_visit.owner = self.request.user
                    site_visit.collector = self.request.user.username
                    clear_finished_search_process()

                site_visit_taxon.save()

        if updated_site_visit_taxon:
            deleted_site_visit_taxon = SiteVisitTaxon.objects.filter(
                site=site_visit.location_site,
                site_visit=site_visit,
                collection_date=date
            ).exclude(id__in=updated_site_visit_taxon)
            deleted_site_visit_biotope_taxon = (
                SiteVisitBiotopeTaxon.objects.filter(
                    site_visit=site_visit,
                    date=date
                ).exclude(id__in=updated_site_visit_biotope_taxon)
            )
            deleted_site_visit_biotope_taxon.delete()
            deleted_site_visit_taxon.delete()

    @method_decorator(login_required)
    def post(self, request, *args, **kwargs):
        site_id = kwargs.get('site_id', None)
        sass_id = kwargs.get('sass_id', None)
        signals.post_save.disconnect(
            location_site_post_save_handler,
        )
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
        elif data_source_name:
            data_source, data_source_created = (
                DataSource.objects.get_or_create(
                    name=data_source_name
                )
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

        new_site_visit = not sass_id and site_id
        if new_site_visit:
            site_visit = SiteVisit.objects.create(
                owner=self.request.user,
                location_site_id=site_id
            )
        else:
            site_visit = SiteVisit.objects.get(
                pk=sass_id
            )

        biotope_fractions = self.get_biotope_fractions(self.request.POST)
        sass_biotope_fractions = SassBiotopeFraction.objects.filter(
            sass_biotope__in=[s.sass_biotope.id for s in biotope_fractions]
        )
        site_visit.sass_biotope_fraction.remove(*sass_biotope_fractions)
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

        # Send email to superusers
        if new_site_visit:
            ctx = {
                'owner': self.request.user,
                'assessor': site_visit.assessor,
                'sass_version': site_visit.sass_version,
                'site_visit_date': site_visit.site_visit_date.strftime(
                    '%m/%d/%Y'),
                'site_visit_id': site_visit.id,
                'current_site': Site.objects.get_current()
            }
            staffs = get_user_model().objects.filter(is_superuser=True)
            email_template = 'notifications/sass_created'
            subject = render_to_string(
                '{0}_subject.txt'.format(email_template),
                ctx
            )
            email_body = render_to_string(
                '{0}_message.txt'.format(email_template),
                ctx
            )
            msg = EmailMultiAlternatives(
                subject,
                email_body,
                settings.DEFAULT_FROM_EMAIL,
                list(staffs.values_list('email', flat=True)))
            msg.send()

        signals.post_save.connect(
            location_site_post_save_handler,
        )
        if site_id:
            url = '{base_url}?{querystring}'.format(
                base_url=reverse('sass-form-page', kwargs={
                    'site_id': site_id, }),
                querystring='sass_created_id={}'.format(
                    site_visit.id
                )
            )
            return redirect(url)
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
        if self.sass_version == 4:
            taxon_filters['score__isnull'] = False
        else:
            taxon_filters['sass_5_score__isnull'] = False
        sass_taxon_list = SassTaxon.objects.annotate(
            name=Case(
                When(taxon_sass_4__isnull=False,
                     then=F('taxon_sass_4')),
                default=F('taxon_sass_5'))
        ).filter(**taxon_filters).order_by(
            'display_order_sass_%s' % self.sass_version
        )
        if self.site_visit:
            biotope_taxon_list = (
                self.site_visit.sitevisitbiotopetaxon_set.all()
            )
            site_visit_taxon_list = (
                dict((self.site_visit.sitevisittaxon_set.all()).values_list(
                    'sass_taxon__id',
                    'taxon_abundance__abc'))
            )

        last_taxon_group = ''
        bold_bottom_border = False
        for sass_taxon in sass_taxon_list:
            if self.sass_version == 5:
                sass_taxon_score = sass_taxon.sass_5_score
            else:
                sass_taxon_score = sass_taxon.score
            sass_taxon_name = sass_taxon.name
            try:
                taxonomies = Taxonomy.objects.filter(
                    canonical_name__icontains=sass_taxon.taxon.canonical_name
                )
                group = (
                    TaxonGroup.objects.filter(
                        taxonomies__in=list(
                            taxonomies.values_list('id', flat=True)),
                        category=TaxonomicGroupCategory.SASS_TAXON_GROUP.name
                    )[0].name
                )
                if last_taxon_group != group:
                    last_taxon_group = group
                    bold_bottom_border = True
                else:
                    bold_bottom_border = False
                    group = ''
            except IndexError:
                group = ''
                bold_bottom_border = False

            taxon_dict = {
                'name': sass_taxon_name.upper(),
                'id': sass_taxon.id,
                'group': group,
                'score': sass_taxon_score,
                'bold_bottom_border': bold_bottom_border,
                'rating_scale': sass_taxon.rating_scale,
                's_value': None,
                'veg_value': None,
                'gsm_value': None,
                'tot_value': None,
            }

            if not self.site_visit:
                taxon_list_form.append(taxon_dict)
                continue

            sass_taxon_biotope_list = biotope_taxon_list.filter(
                sass_taxon=sass_taxon).values_list(
                'biotope__name',
                'taxon_abundance__abc')

            empty_taxon_biotope_value = True
            if sass_taxon_biotope_list:
                empty_taxon_biotope_value = False
                for sass_taxon_biotope in sass_taxon_biotope_list:
                    biotope_name = sass_taxon_biotope[0].lower()
                    biotope_value = sass_taxon_biotope[1]
                    biotope_identifier = self.check_biotope(
                        biotope_name
                    )
                    if biotope_identifier == BIOTOPE_STONES:
                        taxon_dict['s_value'] = biotope_value
                    elif biotope_identifier == BIOTOPE_GSM:
                        taxon_dict['gsm_value'] = biotope_value
                    elif biotope_identifier == BIOTOPE_VEGETATION:
                        taxon_dict['veg_value'] = biotope_value
            if sass_taxon.id in site_visit_taxon_list:
                empty_taxon_biotope_value = False
                taxon_dict['tot_value'] = (
                    site_visit_taxon_list[sass_taxon.id]
                )
            # If read only, don't show empty taxon row
            if self.read_only and empty_taxon_biotope_value:
                continue
            taxon_list_form.append(taxon_dict)
        return taxon_list_form

    def check_biotope(self, biotope_name):
        """
        Check which biotope this data belongs to
        :param biotope_name: biotope name, e.g. 'vegetation'
        :return: general biotope name
        """
        stones_identifier = ['sic', 'sooc', 'stones']
        veg_identifier = ['vegetation', 'mv', 'aqv', 'mvic', 'mvoc']
        gsm_identifier = ['g/s/m', 'gravel', 'sand', 'silt/mud/clay']
        biotope_name = biotope_name.lower()

        for stone in stones_identifier:
            if stone in biotope_name:
                return BIOTOPE_STONES
        for veg in veg_identifier:
            if veg in biotope_name:
                return BIOTOPE_VEGETATION
        for gsm in gsm_identifier:
            if gsm in biotope_name:
                return BIOTOPE_GSM

    def get_context_data(self, **kwargs):
        context = super(SassFormView, self).get_context_data(**kwargs)

        sass_created_id = self.request.GET.get('sass_created_id', None)
        if sass_created_id:
            try:
                sass_created = SiteVisit.objects.get(
                    id=sass_created_id
                )
                context['alert'] = (
                    'New SASS data has been added : '
                    '<a href="/sass/view/{0}">{1}</a>'.format(
                        sass_created_id,
                        sass_created.site_visit_date
                    )
                )
            except SiteVisit.DoesNotExist:
                pass

        if self.site_visit:
            context['is_update'] = True
            context['site_visit_id'] = self.site_visit.id
            context['assessor'] = self.site_visit.assessor
            context['date'] = self.site_visit.site_visit_date
            context['time'] = self.site_visit.time
            context['owner'] = self.site_visit.owner
            if self.site_visit.comments_or_observations:
                context['comments'] = self.site_visit.comments_or_observations
            if self.site_visit.other_biota:
                context['other_biota'] = self.site_visit.other_biota
            context['data_source'] = self.site_visit.data_source

        context['biotope_form_list'] = self.get_biotope_form_data()
        context['taxon_list'] = self.get_taxon_list()
        context['site_code'] = self.site_code
        if self.site_visit:
            context['sass_version'] = self.site_visit.sass_version

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
            self.sass_version = int(request.GET.get('sass_version', 5))
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


class SassReadFormView(SassFormView):
    template_name = 'form_only_read_page.html'
    read_only = True

    def test_func(self):
        return True

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
        return super(SassFormView, self).get(
            request, *args, **kwargs
        )


class SassDeleteView(UserPassesTestMixin, View):
    def test_func(self):
        if self.request.user.is_anonymous:
            return False
        if self.request.user.is_superuser:
            return True
        sass_id = self.kwargs.get('sass_id', None)
        if not sass_id:
            return True
        return SiteVisit.objects.filter(
            Q(owner=self.request.user) | Q(assessor=self.request.user),
            id=sass_id,).exists()

    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        return super(SassDeleteView, self).dispatch(request, *args, **kwargs)

    @method_decorator(login_required)
    def post(self, request, *args, **kwargs):
        site_visit = get_object_or_404(
            SiteVisit,
            id=kwargs.get('sass_id', None)
        )
        site_visit.delete()
        messages.success(
            request,
            'SASS record successfully deleted!',
            extra_tags='sass_record')
        redirect_url = '/sass/dashboard/{0}/?siteId={0}'.format(
            site_visit.location_site.id
        )
        return HttpResponseRedirect(redirect_url)
