from django.views.generic import TemplateView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.shortcuts import redirect
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.contrib.auth.mixins import UserPassesTestMixin
from bims.models.location_site import LocationSite
from sass.models import SassTaxon, SASS5Sheet, SASS5Record
from sass.enums.sass5_rating import SASS5Rating


class FormView(UserPassesTestMixin, TemplateView):
    """Template view for landing page"""
    template_name = 'form_page.html'
    post_dictionary = {}

    def test_func(self):
        sass_id = self.kwargs.get('sass_id', None)
        if not sass_id:
            return True
        return SASS5Sheet.objects.filter(
            id=sass_id,
            owner=self.request.user).exists()

    @method_decorator(login_required)
    def post(self, request, *args, **kwargs):
        site_id = kwargs.get('site_id', None)
        sass_id = kwargs.get('sass_id', None)
        self.post_dictionary = request.POST.dict()
        time_min = self.post_dictionary.get('time-min', None)
        try:
            time_min = int(time_min)
        except ValueError:
            time_min = None
        sic_rating = self.get_rating('sic-rating')
        sooc_rating = self.get_rating('sooc-rating')
        bedrock_rating = self.get_rating('bedrock-rating')
        aquatic_veg_rating = self.get_rating('aquatic-veg-rating')
        mic_rating = self.get_rating('mic-rating')
        mooc_rating = self.get_rating('mooc-rating')
        gravel_rating = self.get_rating('gravel-rating')
        mud_rating = self.get_rating('mud-rating')
        sand_rating = self.get_rating('sand-rating')
        hand_picking_rating = self.get_rating('hand-picking-rating')
        owner = request.user

        if not sass_id and site_id:
            sass_5_sheet = SASS5Sheet.objects.create(
                owner=owner,
                location_site_id=site_id
            )
        else:
            sass_5_sheet = SASS5Sheet.objects.get(
                pk=sass_id
            )

        sass_5_sheet.time_minutes = time_min
        sass_5_sheet.biotope_stones_in_current = sic_rating
        sass_5_sheet.biotope_stones_out_of_current = sooc_rating
        sass_5_sheet.biotope_bedrock = bedrock_rating
        sass_5_sheet.biotope_aquatic_vegetation = aquatic_veg_rating
        sass_5_sheet.biotope_margin_veg_in_current = mic_rating
        sass_5_sheet.biotope_margin_veg_out_of_current = mooc_rating
        sass_5_sheet.biotope_gravel = gravel_rating
        sass_5_sheet.biotope_mud = mud_rating
        sass_5_sheet.biotope_sand = sand_rating
        sass_5_sheet.biotope_hand_picking = hand_picking_rating
        sass_5_sheet.notes = request.POST.get('notes', None)
        sass_5_sheet.other_biota = request.POST.get('other-biota', None)
        sass_5_sheet.save()

        # Sass 5 records
        sass_5_taxa = SassTaxon.objects.filter(
            taxon_sass_5__isnull=False
        ).order_by('display_order_sass_5')
        for sass_5_taxon in sass_5_taxa:
            sass_5_record_data = self.get_sass_5_record_data(sass_5_taxon.id)
            if sass_5_record_data:
                sass_5_record, created = SASS5Record.objects.get_or_create(
                    sass_sheet=sass_5_sheet,
                    taxonomy=sass_5_taxon
                )
                for key, value in sass_5_record_data.iteritems():
                    setattr(sass_5_record, key, value)
                sass_5_record.save()

        if site_id:
            return redirect(
                reverse('sass-form-page', kwargs={'site_id': site_id}))
        else:
            return redirect(
                reverse('sass-update-page', kwargs={'sass_id': sass_id})
            )

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

    def get_context_data(self, **kwargs):
        context = super(FormView, self).get_context_data(**kwargs)
        sass_id = kwargs.get('sass_id', None)
        sass_5_records = None
        if sass_id:
            sass_5_records = SASS5Record.objects.filter(
                sass_sheet_id=sass_id
            )
        sass_5_taxa = SassTaxon.objects.filter(
            taxon_sass_5__isnull=False
        ).order_by('display_order_sass_5')
        taxon_list = []
        for sass_5_taxon in sass_5_taxa:
            sass_5_record_taxon = None
            if sass_5_records:
                sass_5_record_taxon = sass_5_records.filter(
                    taxonomy=sass_5_taxon
                )
            taxon_dict = {
                'name': sass_5_taxon.taxon_sass_5,
                'id': sass_5_taxon.id,
                'has_score': (
                    False if sass_5_taxon.sass_5_score is None else True
                ),
                'should_bold': (
                    sass_5_taxon.taxon_sass_5.split(' ')[0].isupper()
                ),
                's_value': None,
                'veg_value': None,
                'gsm_value': None,
                'tot_value': None,
            }
            if sass_5_record_taxon:
                taxon_dict['s_value'] = sass_5_record_taxon[0].stone_and_rock
                taxon_dict['veg_value'] = (
                    sass_5_record_taxon[0].vegetation
                )
                taxon_dict['gsm_value'] = (
                    sass_5_record_taxon[0].gravel_sand_mud
                )
                taxon_dict['tot_value'] = (
                    sass_5_record_taxon[0].count
                )
            taxon_list.append(taxon_dict)
        context['taxon_list'] = taxon_list

        if sass_id:
            sass_sheet = SASS5Sheet.objects.filter(pk=sass_id)
            context['sass_sheet'] = sass_sheet.values()[0]
        return context

    @method_decorator(login_required)
    def get(self, request, *args, **kwargs):
        site_id = kwargs.get('site_id')
        sass_id = kwargs.get('sass_id')
        self.post_dictionary = {}
        if site_id:
            get_object_or_404(
                LocationSite,
                pk=site_id
            )
        else:
            get_object_or_404(
                SASS5Sheet,
                pk=sass_id
            )
        return super(FormView, self).get(request, *args, **kwargs)
