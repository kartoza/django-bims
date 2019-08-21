import uuid
import json
import logging
import time
from datetime import datetime
from dateutil.parser import parse
from django.contrib.auth import get_user_model
from django.views.generic import TemplateView
from django.contrib.auth.decorators import login_required
from django.contrib.gis.geos import Point
from django.utils.decorators import method_decorator
from django.db.models import F
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.http import HttpResponseRedirect, Http404
from bims.utils.get_key import get_key
from bims.models import (
    LocationSite, Biotope, SamplingMethod,
    BiologicalCollectionRecord,
    Taxonomy,
    LocationType,
    TaxonGroup,
    SiteImage
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

    @staticmethod
    def get_last_session(request):
        try:
            return request.session['%s-fish-uploader' % request.user.username]
        except KeyError:
            return None

    @staticmethod
    def add_last_session(request, session_uuid, data):
        try:
            session_data = request.session[
                '%s-fish-uploader' % request.user.username]
        except KeyError:
            session_data = {}
        session_data[session_uuid] = data
        request.session[
            '%s-fish-uploader' % request.user.username] = session_data

    @staticmethod
    def remove_session(request, session_uuid):
        try:
            session_data = request.session[
                '%s-fish-uploader' % request.user.username]
            del session_data[session_uuid]
            request.session[
                '%s-fish-uploader' % request.user.username] = session_data
        except KeyError:
            pass

    def all_fishes(self, fish_parents):
        """
        Get all fishes
        :param fish_parents: list of fish parent id
        :return: array of taxa id
        """
        fish_list = []
        fishes = Taxonomy.objects.filter(
            parent__in=fish_parents
        )
        if fishes:
            fish_list = list(fishes.values_list('id', flat=True))
            fish_list.extend(self.all_fishes(fishes))
        return fish_list

    def taxa_from_river_catchment(self):
        """
        Get taxa from nearest river_catchment
        :return: list of taxa
        """
        river_catchment_value = None
        river_catchment_query = None
        fish_group, created = TaxonGroup.objects.get_or_create(
            name='Fish'
        )
        all_fishes = self.all_fishes(fish_group.taxonomies.all())

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
                ).distinct('taxon_name').filter(
                    taxon_id__isnull=False,
                    taxon_id__in=all_fishes,
                ).order_by(
                    'taxon_name'
                )
            )
        return taxa_list

    def get_context_data(self, **kwargs):
        context = super(FishFormView, self).get_context_data(**kwargs)
        if not self.location_site:
            return context
        context['geoserver_public_location'] = get_key(
            'GEOSERVER_PUBLIC_LOCATION')
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
            Biotope.objects.filter(
                taxon_group__name__icontains='fish',
                taxon_group__category='SPECIES_MODULE').values(
                'name', 'description', 'display_order'
            ).order_by('display_order')
        )

        sampling_method_lower_list = []
        context['sampling_method_list'] = []
        sampling_method_list = list(
            SamplingMethod.objects.all().values(
                'id', 'sampling_method'
            ).order_by(F('normalisation_factor').asc(nulls_first=True))
        )
        for sampling_method in sampling_method_list:
            sampling_method_name = (
                sampling_method['sampling_method'].replace('-', ' ')
            ).strip()
            if sampling_method_name.lower() not in sampling_method_lower_list:
                sampling_method_lower_list.append(sampling_method_name.lower())
                context['sampling_method_list'].append(sampling_method)

        return context

    @method_decorator(login_required)
    def get(self, request, *args, **kwargs):
        site_id = request.GET.get('siteId', None)
        if site_id:
            self.location_site = get_object_or_404(
                LocationSite,
                pk=site_id
            )
        else:
            raise Http404()

        return super(FishFormView, self).get(request, *args, **kwargs)

    @method_decorator(login_required)
    def post(self, request, *args, **kwargs):
        date_string = request.POST.get('date', None)
        collector = request.POST.get('collector', '')
        collector_id = request.POST.get('collector_id', '').strip()
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

        # Create or get location site
        site_name = post_data.get('site_name', '')
        site_code = post_data.get('site_code', '')
        site_description = post_data.get('site_description', '')
        latitude = post_data.get('latitude', 0.0)
        longitude = post_data.get('longitude', 0.0)
        site_point = Point(
            float(longitude),
            float(latitude))

        # If collector id exist then get the user object
        collector_user = None
        if collector_id:
            try:
                collector_user = get_user_model().objects.get(
                    id=int(collector_id))
            except get_user_model().DoesNotExist:
                pass

        if site_name or site_code:
            location_type, created = LocationType.objects.get_or_create(
                name='PointObservation',
                allowed_geometry='POINT'
            )
            self.location_site, status = LocationSite.objects.get_or_create(
                name=site_name,
                site_code=site_code,
                site_description=site_description,
                location_type=location_type,
                geometry_point=site_point
            )
        else:
            self.location_site = LocationSite.objects.get(
                id=post_data.get('site-id', None)
            )

        site_image_file = request.FILES.get('site-image', None)
        if site_image_file:
            SiteImage.objects.get_or_create(
                site=self.location_site,
                image=site_image_file
            )
        taxa_id_list = post_data.get('taxa-id-list', '').split(',')
        taxa_id_list = filter(None, taxa_id_list)

        collection_record_ids = []
        for taxon in taxa_id_list:
            observed_key = '{}-observed'.format(taxon)
            abundance_key = '{}-abundance'.format(taxon)
            sampling_method_key = '{}-sampling-method'.format(
                taxon
            )
            taxonomy = Taxonomy.objects.get(
                id=taxon
            )
            sampling_method_id = post_data[sampling_method_key]
            sampling_effort = '{effort} {type}'.format(
                effort=post_data[
                    '{}-sampling-effort'.format(taxon)],
                type=post_data[
                    '{}-sampling-effort-type'.format(taxon)]
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
                            collector_user=collector_user,
                            sampling_method=sampling_method,
                            abundance_number=abundance,
                            owner=self.request.user,
                            biotope=biotope,
                            reference=reference,
                            reference_category=reference_category,
                            sampling_effort=sampling_effort
                        )
                    )
                    collection_record_ids.append(collection_record.id)
                    if status:
                        logger.info(
                            'Collection record added with id {}'.format(
                                collection_record.id
                            )
                        )
            except KeyError:
                continue

        session_uuid = '%s' % uuid.uuid4()
        FishFormView.add_last_session(request, session_uuid, {
            'edited_at': int(time.mktime(datetime.now().timetuple())),
            'records': collection_record_ids,
            'location_site': self.location_site.name,
            'form': 'fish-form'
        })
        url = reverse('source-reference-form') + '?session=' + session_uuid
        return HttpResponseRedirect(url)
