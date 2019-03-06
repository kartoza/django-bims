import json
import logging
from dateutil.parser import parse
from django.views.generic import TemplateView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.db.models import F
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.http import HttpResponseRedirect
from bims.models import (
    LocationSite, Biotope, SamplingMethod,
    BiologicalCollectionRecord,
    Taxonomy
)

logger = logging.getLogger('bims')

RIVER_CATCHMENT_ORDER = [
    'quinary_catchment_area',
    'quaternary_catchment_area',
    'tertiary_catchment_area',
    'secondary_catchment_area',
    'primary_catchment_area',
]


class FishFormView(TemplateView):
    """View for fish form"""
    template_name = 'fish_form_page.html'
    location_site = None

    def taxa_from_river_catchment(self):
        """
        Get taxa from river_catchment
        :return: list of taxa
        """
        river_catchment_value = None
        river_catchment_query = None
        try:
            location_site_context = json.loads(
                self.location_site.location_context)
            water_group = (
                location_site_context['context_group_values']['water_group']
                ['service_registry_values']
            )
            for river_catchment in RIVER_CATCHMENT_ORDER:
                if river_catchment in water_group:
                    river_catchment_value = (
                        water_group[river_catchment]['value']
                    )
                    river_catchment_query = (
                            'location_context__'
                            'context_group_values__water_group__'
                            'service_registry_values__%s__value' %
                            river_catchment
                    )
                    break
        except (KeyError, TypeError) as e:
            logger.error(e)
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
                ).distinct('biological_collection_record__taxonomy').filter(
                    taxon_id__isnull=False
                )
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
        context['taxa'] = self.taxa_from_river_catchment()
        context['reference_category'] = list(
            BiologicalCollectionRecord.objects.filter(
                reference_category__isnull=False).exclude(
                reference_category='').distinct(
                'reference_category').values(
                name=F('reference_category'))
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
        collector = request.POST.get('collector', '')
        biotope_id = request.POST.get('biotope', None)
        reference = request.POST.get('study_reference', '')
        reference_category = request.POST.get('reference_category', '')
        biotope = None
        if biotope_id:
            biotope = Biotope.objects.get(
                id=biotope_id
            )
        collection_date = parse(date_string)
        post_data = request.POST.dict()
        self.location_site = LocationSite.objects.get(
            id=post_data.get('site-id', None)
        )
        taxa_list = self.taxa_from_river_catchment()
        for taxon in taxa_list:
            observed_key = '{}-observed'.format(taxon['taxon_id'])
            abundance_key = '{}-abundance'.format(taxon['taxon_id'])
            sampling_method_key = '{}-sampling-method'.format(
                taxon['taxon_id']
            )
            taxonomy = Taxonomy.objects.get(
                id=taxon['taxon_id']
            )
            sampling_method_id = post_data[sampling_method_key]
            sampling_effort = '{effort} {type}'.format(
                effort=post_data[
                    '{}-sampling-effort'.format(taxon['taxon_id'])],
                type=post_data[
                    '{}-sampling-effort-type'.format(taxon['taxon_id'])]
            )
            try:
                if post_data[observed_key] == 'True':
                    sampling_method = None
                    if sampling_method_id:
                        sampling_method = SamplingMethod.objects.get(
                            id=sampling_method_id
                        )
                    abundance = post_data[abundance_key]
                    collection_record, status = (
                        BiologicalCollectionRecord.objects.get_or_create(
                            collection_date=collection_date,
                            taxonomy=taxonomy,
                            original_species_name=taxonomy.canonical_name,
                            site=self.location_site,
                            collector=collector,
                            sampling_method=sampling_method,
                            abundance_number=abundance,
                            owner=self.request.user,
                            biotope=biotope,
                            reference=reference,
                            reference_category=reference_category,
                            sampling_effort=sampling_effort
                        )
                    )
                    if status:
                        logger.info(
                            'Collection record added with id {}'.format(
                                collection_record.id
                            )
                        )
            except KeyError:
                continue

        return HttpResponseRedirect(reverse('nonvalidated-user-list'))
