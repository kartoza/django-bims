from django.views.generic import TemplateView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.shortcuts import redirect
from django.shortcuts import get_object_or_404
from django.urls import reverse
from bims.models.location_site import LocationSite
from sass.models import SassTaxon, SASS5Sheet, SASS5Record
from sass.enums.sass5_rating import SASS5Rating


class FormView(TemplateView):
    """Template view for landing page"""
    template_name = 'form_page.html'
    post_dictionary = {}

    @method_decorator(login_required)
    def post(self, request, *args, **kwargs):
        site_id = kwargs.get('site_id', None)
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
        sass_5_sheet = SASS5Sheet.objects.create(
            owner=owner,
            time_minutes=time_min,
            biotope_stones_in_current=sic_rating,
            biotope_stones_out_of_current=sooc_rating,
            biotope_bedrock=bedrock_rating,
            biotope_aquatic_vegetation=aquatic_veg_rating,
            biotope_margin_veg_in_current=mic_rating,
            biotope_margin_veg_out_of_current=mooc_rating,
            biotope_gravel=gravel_rating,
            biotope_mud=mud_rating,
            biotope_sand=sand_rating,
            biotope_hand_picking=hand_picking_rating,
            location_site_id=site_id,
            notes=request.POST.get('notes', None),
            other_biota=request.POST.get('other-biota', None)
        )

        # Sass 5 records
        sass_5_taxa = SassTaxon.objects.filter(
            taxon_sass_5__isnull=False
        ).order_by('display_order_sass_5')
        for sass_5_taxon in sass_5_taxa:
            sass_5_record_data = self.get_sass_5_record_data(sass_5_taxon.id)
            if sass_5_record_data:
                SASS5Record.objects.create(
                    sass_sheet=sass_5_sheet,
                    taxonomy=sass_5_taxon,
                    **sass_5_record_data
                )

        return redirect(
            reverse('sass-form-page', kwargs={'site_id': site_id}))

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
        sass_5_taxa = SassTaxon.objects.filter(
            taxon_sass_5__isnull=False
        ).order_by('display_order_sass_5')
        taxon_list = []
        for sass_5_taxon in sass_5_taxa:
            taxon_list.append({
                'name': sass_5_taxon.taxon_sass_5,
                'id': sass_5_taxon.id,
                'has_score': (
                    False if sass_5_taxon.sass_5_score is None else True
                ),
                'should_bold': (
                    sass_5_taxon.taxon_sass_5.split(' ')[0].isupper()
                )
            })
        context['taxon_list'] = taxon_list
        return context

    @method_decorator(login_required)
    def get(self, request, *args, **kwargs):
        site_id = kwargs.get('site_id')
        self.post_dictionary = {}
        get_object_or_404(
            LocationSite,
            pk=site_id
        )
        return super(FormView, self).get(request, *args, **kwargs)
