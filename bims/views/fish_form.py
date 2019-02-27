import json
from django.views.generic import TemplateView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.db.models import F
from django.shortcuts import get_object_or_404
from bims.models import LocationSite, Biotope
from sass.models import SamplingMethod

RIVER_CATCHMENT_ORDER = [
    'primary_catchment_area',
    'secondary_catchment_area',
    'tertiary_catchment_area',
    'quaternary_catchment_area',
    'quinary_catchment_area'
]


class FishFormView(TemplateView):
    """View for fish form"""
    template_name = 'fish_form_page.html'
    location_site = None

    def get_taxa_from_river_catchment(self):
        river_catchment_value = None
        river_catchment_query = None
        location_site_context = json.loads(self.location_site.location_context)
        try:
            water_group = (
                location_site_context['context_group_values']['water_group']
                ['service_registry_values']
            )
            river_catchment_order = RIVER_CATCHMENT_ORDER
            river_catchment_order.reverse()
            for river_catchment in river_catchment_order:
                if river_catchment in water_group:
                    river_catchment_value = (
                        water_group[river_catchment]['value']
                    )
                    river_catchment_query = (
                        'location_context__'
                        'context_group_values__water_group__'
                        'service_registry_values__%s__value' % river_catchment
                    )
                    break
        except KeyError:
            pass

        taxa_list = []
        if river_catchment_value and river_catchment_query:
            taxa_list = list(
                LocationSite.objects.filter(**{
                    river_catchment_query: river_catchment_value
                }).values(
                    taxon_id=F('biological_collection_record__taxonomy'),
                    taxon_name=F(
                        'biological_collection_record__taxonomy__'
                        'canonical_name'),
                    rank=F('biological_collection_record__taxonomy__rank')
                ).distinct('biological_collection_record__taxonomy')
            )
        return taxa_list

    def get_context_data(self, **kwargs):
        context = super(FishFormView, self).get_context_data(**kwargs)
        if not self.location_site:
            return context
        context['location_site_name'] = self.location_site.name
        context['location_site_code'] = self.location_site.site_code
        context['location_site_lat'] = self.location_site.get_centroid().y
        context['location_site_long'] = self.location_site.get_centroid().x
        context['site_id'] = self.location_site.id
        context['taxa'] = list(
            self.location_site.biological_collection_record.values(
                taxon_id=F('taxonomy'),
                taxon_name=F(
                    'taxonomy__'
                    'canonical_name'),
                rank=F('taxonomy__rank')
            ).distinct('taxonomy')
        )
        context['biotope_list'] = list(
            Biotope.objects.all().values(
                'name', 'description', 'display_order'
            ).order_by('display_order')
        )
        context['sampling_method_list'] = list(
            SamplingMethod.objects.all().values(
                'id', 'sampling_method'
            ).order_by(F('normalisation_factor').asc(nulls_first=True))
        )
        return context

    @method_decorator(login_required)
    def get(self, request, *args, **kwargs):
        site_id = request.GET.get('siteId', None)
        if site_id:
            self.location_site = get_object_or_404(
                LocationSite,
                pk=site_id
            )

        return super(FishFormView, self).get(request, *args, **kwargs)

    @method_decorator(login_required)
    def post(self, request, *args, **kwargs):
        date_string = request.POST.get('date', None)
        post_data = request.POST.dict()
        location_site = LocationSite.objects.get(
            post_data.get('site-id', None)
        )
        taxa_list = list(
            location_site.biological_collection_record.values(
                taxon_id=F('taxonomy'),
                taxon_name=F(
                    'taxonomy__'
                    'canonical_name'),
                rank=F('taxonomy__rank')
            ).distinct('taxonomy')
        )
        for taxon in taxa_list:
            observed_key = '{}-observed'.format(taxon.taxon_id)
            abundance_key = '{}-abundance'.format(taxon.taxon_id)
            sampling_method_key = '{}-sampling-method'.format(
                taxon.taxon_id
            )
            try:
                if post_data[observed_key]:
                    pass
            except KeyError:
                continue
