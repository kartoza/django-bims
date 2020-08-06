import re
import time
import uuid
from datetime import datetime as libdatetime
from dateutil.parser import parse
from django.db.models import Case, When, F, Q, signals
from django.views.generic import TemplateView, View
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.utils import timezone
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
from bims.models.survey import Survey
from bims.models.chemical_record import ChemicalRecord
from bims.models.profile import Profile as BimsProfile
from bims.models.taxonomy import Taxonomy
from bims.models.biotope import Biotope
from bims.models.data_source import DataSource
from bims.models.site_image import SiteImage
from bims.models.taxon_group import TaxonGroup
from bims.utils.get_key import get_key
from sass.models import (
    SiteVisit,
    SassTaxon,
    SiteVisitBiotopeTaxon,
    SiteVisitTaxon,
    TaxonAbundance,
    Rate,
    SassBiotopeFraction
)
from bims.views.mixin.session_form.mixin import SessionFormMixin
from bims.utils.search_process import clear_finished_search_process

from bims.enums import TaxonomicGroupCategory

BIOTOPE_STONES = 'SIC/SOOC'
BIOTOPE_VEGETATION = 'MV/AQV'
BIOTOPE_GSM = 'G/S/M'

# Biotope Sampled Sheet
BSS_STONES_IN_CURRENT = 'Stones in current (SIC)'
BSS_STONES_OUT_OF_CURRENT = 'Stones out of current (SOOC)'


class SassFormView(UserPassesTestMixin, TemplateView, SessionFormMixin):
    """Template view for Sass Form"""
    template_name = 'form_page.html'
    post_dictionary = {}
    site_visit = SiteVisit.objects.none()
    sass_version = 5
    site_code = ''
    site_lat = None
    site_lon = None
    read_only = False
    source_collection = None
    session_identifier = 'sass-form'

    def __init__(self, *args, **kwargs):
        super(SassFormView, self).__init__(*args, **kwargs)
        taxon_groups = TaxonGroup.objects.filter(
            name__icontains='Invertebrates'
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
            Q(owner=self.request.user) |
            Q(collector=self.request.user),
            id=sass_id,).exists()

    def get_biotope_fractions(self, post_dictionary):
        # Get biotope fractions
        biotope_fractions = []
        biotope_list = dict(
            Biotope.objects.filter(biotope_form=1).values_list(
                'name', 'id'
            ))
        for biotope_key, biotope_id in biotope_list.iteritems():
            biotope_key = re.sub(r'\([^)]*\)', '', biotope_key).strip()
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
                try:
                    site_visit_biotope_taxon, status = (
                        SiteVisitBiotopeTaxon.objects.get_or_create(
                            site_visit=site_visit,
                            sass_taxon=sass_taxon,
                            taxon=sass_taxon.taxon,
                            biotope=biotope,
                        )
                    )
                except SiteVisitBiotopeTaxon.MultipleObjectsReturned:
                    # There shouldn't be multiple objects returned,
                    # but just in case, remove the new one
                    site_visit_biotope_taxa = (
                        SiteVisitBiotopeTaxon.objects.filter(
                            site_visit=site_visit,
                            sass_taxon=sass_taxon,
                            taxon=sass_taxon.taxon,
                            biotope=biotope,
                        ).order_by('id')
                    )
                    for to_delete in site_visit_biotope_taxa[1:]:
                        to_delete.delete()
                    site_visit_biotope_taxon = site_visit_biotope_taxa[0]
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
                            validated=True
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
                site_visit_taxon.owner = site_visit.owner
                site_visit_taxon.collector_user = site_visit.collector
                site_visit_taxon.source_collection = self.source_collection

                if created:
                    site_visit.owner = self.request.user
                    clear_finished_search_process()

                site_visit_taxon.save()

        if updated_site_visit_taxon:
            deleted_site_visit_taxon = SiteVisitTaxon.objects.filter(
                site_visit=site_visit,
            ).exclude(id__in=updated_site_visit_taxon)
            deleted_site_visit_biotope_taxon = (
                SiteVisitBiotopeTaxon.objects.filter(
                    site_visit=site_visit,
                ).exclude(id__in=updated_site_visit_biotope_taxon)
            )
            deleted_site_visit_biotope_taxon.delete()
            deleted_site_visit_taxon.delete()

        return updated_site_visit_taxon

    def create_or_get_survey(self, site_visit, site_visit_taxa):
        """Get or create a site survey"""
        survey = None
        # Check duplicate data
        existing_surveys = Survey.objects.filter(
            owner=site_visit.owner,
            date=site_visit.site_visit_date,
            site=site_visit.location_site)
        if existing_surveys.count() > 1:
            survey = existing_surveys[0]
            ChemicalRecord.objects.filter(
                survey__in=existing_surveys
            ).update(survey=survey)
            Survey.objects.filter(
                id__in=existing_surveys
            ).exclude(id=survey.id).delete()
        elif existing_surveys.count() == 1:
            survey = existing_surveys[0]
        if not survey and site_visit_taxa:
            surveys = list(
                site_visit_taxa.filter(survey__isnull=False).values_list(
                    'survey', flat=True).distinct('survey')
            )
            if len(surveys) > 0:
                return Survey.objects.get(id=surveys[0])
        if survey:
            return Survey.objects.get(
                id=survey.id
            )
        else:
            survey = Survey.objects.create(
                owner=site_visit.owner,
                date=site_visit.site_visit_date,
                site=site_visit.location_site
            )
            if site_visit_taxa:
                site_visit_taxa.update(survey=survey)
            return survey

    @method_decorator(login_required)
    def post(self, request, *args, **kwargs):
        site_id = kwargs.get('site_id', None)
        sass_id = kwargs.get('sass_id', None)
        signals.post_save.disconnect(
            location_site_post_save_handler,
        )

        # Owner
        owner_id = request.POST.get('owner', None)
        owner = None
        if owner_id:
            try:
                owner = Profile.objects.get(id=int(owner_id))
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
                collector=self.request.user,
                location_site_id=site_id
            )
        else:
            site_visit = SiteVisit.objects.get(
                pk=sass_id
            )

        # Accredited
        accredited = request.POST.get('accredited', False) == 'on'
        if accredited and owner:
            bims_profile = BimsProfile.objects.get(user=owner)
            if not bims_profile.is_accredited(
                collection_date=site_visit.site_visit_date
            ):
                bims_profile.accredit(
                    date_accredit_to=site_visit.site_visit_date
                )

        biotope_fractions = self.get_biotope_fractions(self.request.POST)
        sass_biotope_fractions = SassBiotopeFraction.objects.filter(
            sass_biotope__in=[s.sass_biotope.id for s in biotope_fractions]
        )
        site_visit.sass_biotope_fraction.remove(*sass_biotope_fractions)
        site_visit.sass_biotope_fraction.add(*biotope_fractions)
        site_visit.site_visit_date = date
        site_visit.time = datetime
        site_visit.owner = owner
        site_visit.sass_version = self.sass_version
        site_visit.data_source = data_source
        site_visit.comments_or_observations = request.POST.get(
            'notes', None
        )
        site_visit.other_biota = request.POST.get(
            'other-biota', None
        )
        site_visit.save()
        site_visit_taxon_ids = self.update_site_visit_biotope_taxon(
            site_visit,
            self.request.POST,
            date)

        # upload site image
        try:
            site_image = request.FILES['site_image']
            if site_image:
                try:
                    site_image_obj = SiteImage.objects.get(
                        site_visit=site_visit
                    )
                    site_image_obj.image = site_image
                    site_image_obj.save()
                except SiteImage.DoesNotExist:
                    site_image_obj = SiteImage(
                        site=site_visit.location_site,
                        site_visit=site_visit,
                        image=site_image
                    )
                    site_image_obj.save()
        except:  # noqa
            pass

        # Send email to superusers
        if new_site_visit:
            ctx = {
                'collector': self.request.user,
                'owner': site_visit.owner,
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
            next_url = '{base_url}?{querystring}'.format(
                base_url=reverse('sass-form-page', kwargs={
                    'site_id': site_id, }),
                querystring='sass_created_id={}'.format(
                    site_visit.id
                )
            )
        else:
            next_url = (
                reverse('sass-update-page', kwargs={'sass_id': sass_id})
            )

        session_uuid = '%s' % uuid.uuid4()
        self.add_last_session(request, session_uuid, {
            'edited_at': int(time.mktime(libdatetime.now().timetuple())),
            'records': site_visit_taxon_ids,
            'location_site': site_visit.location_site.name,
            'form': 'sass-form'
        })
        source_reference_url = reverse('source-reference-form') + (
            '?session={session}&identifier={identifier}&next={next}'.format(
                session=session_uuid,
                next=next_url,
                identifier=self.session_identifier
            )
        )

        # Get or create a survey
        survey = self.create_or_get_survey(
            site_visit,
            SiteVisitTaxon.objects.filter(id__in=site_visit_taxon_ids)
        )
        abiotic_url = '{base_url}?survey={survey_id}&next={next}'.format(
            base_url=reverse('abiotic-form'),
            survey_id=survey.id,
            next=source_reference_url
        )

        return HttpResponseRedirect(abiotic_url)


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
            # Remove abbreviations
            biotope_data_name = re.sub(r'\([^)]*\)', '', biotope_data.name)
            biotope_form_list.append({
                'name': biotope_data_name,
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
            context['collector'] = self.site_visit.collector
            context['date'] = self.site_visit.site_visit_date
            context['time'] = self.site_visit.time
            context['site_identifier'] = (
                self.site_visit.location_site.location_site_identifier
            )
            context['site_id'] = self.site_visit.location_site.id
            owner = self.site_visit.owner
            if self.site_visit.comments_or_observations:
                context['comments'] = self.site_visit.comments_or_observations
            if self.site_visit.other_biota:
                context['other_biota'] = self.site_visit.other_biota

            # Get source reference
            site_visit_taxon = SiteVisitTaxon.objects.filter(
                site_visit=self.site_visit, source_reference__isnull=False)
            if site_visit_taxon.exists():
                source_reference = site_visit_taxon[0].source_reference
                context['source_reference'] = source_reference
        else:
            owner = self.request.user

        if owner:
            context['owner'] = owner
            bims_profile, created = BimsProfile.objects.get_or_create(
                user=owner)
            context['accredited'] = bims_profile.is_accredited(
                collection_date=self.site_visit.site_visit_date
            )

        context['biotope_form_list'] = self.get_biotope_form_data()
        context['taxon_list'] = self.get_taxon_list()
        context['site_code'] = self.site_code
        context['location_site_lat'] = self.site_lat
        context['location_site_lon'] = self.site_lon
        context['geoserver_public_location'] = get_key(
            'GEOSERVER_PUBLIC_LOCATION')
        try:
            self.site_image = (
                SiteImage.objects.get(site_visit=self.site_visit))
            context['site_image'] = self.site_image
        except SiteImage.DoesNotExist:
            pass
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
            self.site_lat = location_site.latitude
            self.site_lon = location_site.longitude
            if not self.site_code:
                self.site_code = location_site.name
            self.sass_version = int(request.GET.get('sass_version', 5))
        else:
            self.site_visit = get_object_or_404(
                SiteVisit,
                pk=sass_id
            )
            self.site_code = self.site_visit.location_site.site_code
            self.site_lat = self.site_visit.location_site.latitude
            self.site_lon = self.site_visit.location_site.longitude
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
            self.site_lat = location_site.latitude
            self.site_lon = location_site.longitude
            if not self.site_code:
                self.site_code = location_site.name
            self.sass_version = request.GET.get('sass_version', 5)
        else:
            self.site_visit = get_object_or_404(
                SiteVisit,
                pk=sass_id
            )
            self.site_code = self.site_visit.location_site.site_code
            self.site_lat = self.site_visit.location_site.latitude
            self.site_lon = self.site_visit.location_site.longitude
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
            Q(owner=self.request.user) | Q(collector=self.request.user),
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
