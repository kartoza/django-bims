from django.views.generic import TemplateView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.shortcuts import redirect
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.contrib.auth.mixins import UserPassesTestMixin
from bims.models.location_site import LocationSite
from bims.models.biotope import Biotope
from sass.models import (
    SiteVisit,
    SassTaxon,
    SiteVisitBiotopeTaxon
)
from sass.enums.sass5_rating import SASS5Rating

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

    def test_func(self):
        if self.request.user.is_superuser:
            return True
        sass_id = self.kwargs.get('sass_id', None)
        if not sass_id:
            return True
        return SiteVisit.objects.filter(
            id=sass_id,
            owner=self.request.user).exists()

    @method_decorator(login_required)
    def post(self, request, *args, **kwargs):
        site_id = kwargs.get('site_id', None)
        # sass_id = kwargs.get('sass_id', None)
        # self.post_dictionary = request.POST.dict()
        # time_min = self.post_dictionary.get('time-min', None)
        # try:
        #     time_min = int(time_min)
        # except ValueError:
        #     time_min = None
        # sic_rating = self.get_rating('sic-rating')
        # sooc_rating = self.get_rating('sooc-rating')
        # bedrock_rating = self.get_rating('bedrock-rating')
        # aquatic_veg_rating = self.get_rating('aquatic-veg-rating')
        # mic_rating = self.get_rating('mic-rating')
        # mooc_rating = self.get_rating('mooc-rating')
        # gravel_rating = self.get_rating('gravel-rating')
        # mud_rating = self.get_rating('mud-rating')
        # sand_rating = self.get_rating('sand-rating')
        # hand_picking_rating = self.get_rating('hand-picking-rating')
        # owner = request.user
        #
        # if not sass_id and site_id:
        #     sass_5_sheet = SASS5Sheet.objects.create(
        #         owner=owner,
        #         location_site_id=site_id
        #     )
        # else:
        #     sass_5_sheet = SASS5Sheet.objects.get(
        #         pk=sass_id
        #     )
        #
        # sass_5_sheet.time_minutes = time_min
        # sass_5_sheet.biotope_stones_in_current = sic_rating
        # sass_5_sheet.biotope_stones_out_of_current = sooc_rating
        # sass_5_sheet.biotope_bedrock = bedrock_rating
        # sass_5_sheet.biotope_aquatic_vegetation = aquatic_veg_rating
        # sass_5_sheet.biotope_margin_veg_in_current = mic_rating
        # sass_5_sheet.biotope_margin_veg_out_of_current = mooc_rating
        # sass_5_sheet.biotope_gravel = gravel_rating
        # sass_5_sheet.biotope_mud = mud_rating
        # sass_5_sheet.biotope_sand = sand_rating
        # sass_5_sheet.biotope_hand_picking = hand_picking_rating
        # sass_5_sheet.notes = request.POST.get('notes', None)
        # sass_5_sheet.other_biota = request.POST.get('other-biota', None)
        # sass_5_sheet.save()
        #
        # # Sass 5 records
        # sass_5_taxa = SassTaxon.objects.filter(
        #     taxon_sass_5__isnull=False
        # ).order_by('display_order_sass_5')
        # for sass_5_taxon in sass_5_taxa:
        #     sass_5_record_data = self.get_sass_5_record_data(sass_5_taxon.id)
        #     if sass_5_record_data:
        #         sass_5_record, created = SASS5Record.objects.get_or_create(
        #             sass_sheet=sass_5_sheet,
        #             taxonomy=sass_5_taxon
        #         )
        #         for key, value in sass_5_record_data.iteritems():
        #             setattr(sass_5_record, key, value)
        #         sass_5_record.save()
        #
        # if site_id:
        #     return redirect(
        #         reverse('sass-form-page', kwargs={'site_id': site_id}))
        # else:
        #     return redirect(
        #         reverse('sass-update-page', kwargs={'sass_id': sass_id})
        #     )

    def get_rating(self, field_name):
        """Returns rating enum name from post data"""
        rating = self.post_dictionary.get(field_name, None)
        if rating:
            try:
                rating = SASS5Rating(rating).name
            except ValueError:
                pass
        return rating

    def get_sass_5_record_data(self, taxon_id):
        """Returns a dict for sass_5_record mode
            e.g. : {
                'vegetation': 12,
                'gravel_sand_mud: 1
            }
         """
        sass_5_records = {}
        s_value = self.post_dictionary.get(
            '{taxon_id}-S'.format(taxon_id=taxon_id))
        if s_value:
            sass_5_records['stone_and_rock'] = int(s_value)
        veg_value = self.post_dictionary.get(
            '{taxon_id}-Veg'.format(taxon_id=taxon_id))
        if veg_value:
            sass_5_records['vegetation'] = int(veg_value)
        gsm_value = self.post_dictionary.get(
            '{taxon_id}-GSM'.format(taxon_id=taxon_id))
        if gsm_value:
            sass_5_records['gravel_sand_mud'] = int(gsm_value)
        tot_value = self.post_dictionary.get(
            '{taxon_id}-TOT'.format(taxon_id=taxon_id))
        if tot_value:
            sass_5_records['count'] = int(tot_value)
        return sass_5_records

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
            biotope_rate = None
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
            ).values_list('taxonomy__id', 'taxon_abundance__abc'))

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
                'has_score': (
                    False if sass_taxon_score is None else True
                ),
                's_value': None,
                'veg_value': None,
                'gsm_value': None,
                'tot_value': None,
            }

            if not self.site_visit:
                taxon_list_form.append(taxon_dict)
                continue

            sass_taxon_biotope = dict(biotope_taxon_list.filter(
                taxon=sass_taxon.taxon).values_list(
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
            if sass_taxon.taxon.id in site_visit_taxon_list:
                taxon_dict['tot_value'] = (
                    site_visit_taxon_list[sass_taxon.taxon.id]
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

        context['biotope_form_list'] = self.get_biotope_form_data()
        context['taxon_list'] = self.get_taxon_list()

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
            get_object_or_404(
                LocationSite,
                pk=site_id
            )
            self.sass_version = request.GET.get('sass_version', 5)
        else:
            self.site_visit = get_object_or_404(
                SiteVisit,
                pk=sass_id
            )
            if self.site_visit.sass_version:
                self.sass_version = self.site_visit.sass_version
        return super(SassFormView, self).get(request, *args, **kwargs)
