import uuid
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
from django.contrib.gis.measure import Distance
from django.http import HttpResponseRedirect, Http404
from bims.utils.get_key import get_key
from bims.models import (
    LocationSite, Biotope, SamplingMethod,
    BiologicalCollectionRecord,
    Taxonomy,
    LocationType,
    TaxonGroup,
    SiteImage,
    LocationContext,
    BIOTOPE_TYPE_SPECIFIC,
    BIOTOPE_TYPE_BROAD,
    BIOTOPE_TYPE_SUBSTRATUM,
    Survey,
    Chem, ChemicalRecord
)
from bims.enums.taxonomic_rank import TaxonomicRank
from bims.views.mixin.session_form.mixin import SessionFormMixin
from bims.models.algae_data import AlgaeData

logger = logging.getLogger('bims')

RIVER_CATCHMENT_ORDER = [
    'primary_catchment_area',
]


class CollectionFormView(TemplateView, SessionFormMixin):
    """View for fish form"""
    template_name = 'collections_form_page.html'
    location_site = None
    session_identifier = 'collection-form'
    taxon_group_name = ''
    survey = None
    all_taxa = None

    def get_all_taxa(self, taxon_group):
        """
        Get all taxon
        :param taxon_group: taxon group object
        :return: array of taxa id
        """
        return Taxonomy.objects.filter(
            id__in=BiologicalCollectionRecord.objects.filter(
                module_group=taxon_group
            ).distinct('taxonomy').values_list('taxonomy')
        ).values_list('id', flat=True)

    def nearest_taxa(self):
        """
        Find nearest taxa within radius
        :return: list of taxa
        """
        radius = 25
        return list(LocationSite.objects.filter(
            geometry_point__distance_lte=(
                self.location_site.geometry_point,
                Distance(km=radius))
        ).values(
            taxon_id=F('biological_collection_record__taxonomy'),
            taxon_name=F(
                'biological_collection_record__taxonomy__'
                'canonical_name'),
            rank=F('biological_collection_record__taxonomy__rank')
        ).distinct('taxon_name').filter(
            taxon_id__isnull=False,
            taxon_id__in=self.all_taxa,
        ).order_by(
            'taxon_name'
        ))

    def taxa_from_river_catchment(self):
        """
        Get taxa from nearest river_catchment
        :return: list of taxa
        """
        river_catchment_query = {}
        location_contexts = LocationContext.objects.filter(
            site=self.location_site
        )

        for river_catchment in RIVER_CATCHMENT_ORDER:
            river_catchment_value = location_contexts.value_from_key(
                river_catchment
            )
            if river_catchment_value != '-':
                river_catchment_query = {
                    'locationcontext__value': river_catchment_value
                }

        taxa_list = []
        if river_catchment_query:
            taxa_list = list(
                LocationSite.objects.filter(**river_catchment_query).values(
                    taxon_id=F('biological_collection_record__taxonomy'),
                    taxon_name=F(
                        'biological_collection_record__taxonomy__'
                        'canonical_name'),
                    rank=F('biological_collection_record__taxonomy__rank')
                ).distinct('taxon_name').filter(
                    taxon_id__isnull=False,
                    taxon_id__in=self.all_taxa,
                ).order_by(
                    'taxon_name'
                )
            )
        return taxa_list

    def create_or_get_survey(self, collection_date, owner):
        """Create or get a site survey"""
        surveys = Survey.objects.filter(
            owner=owner,
            date=collection_date,
            collector_user=self.request.user,
            site=self.location_site
        )
        if surveys.exists():
            survey = surveys[0]
            if surveys.count() > 1:
                # Merge survey
                ChemicalRecord.objects.filter(
                    survey__in=surveys).update(
                    survey=survey
                )
                BiologicalCollectionRecord.objects.filter(
                    survey__in=surveys).update(
                    survey=survey
                )
                AlgaeData.objects.filter(
                    survey__in=surveys).update(
                    survey=survey
                )
                surveys.exclude(id=survey.id).delete()
        else:
            survey = Survey.objects.create(
                owner=owner,
                date=collection_date,
                site=self.location_site,
                collector_user=self.request.user
            )
        return survey

    def get_context_data(self, **kwargs):
        context = super(CollectionFormView, self).get_context_data(**kwargs)
        if not self.location_site:
            return context
        context['geoserver_public_location'] = get_key(
            'GEOSERVER_PUBLIC_LOCATION')
        context['location_site_name'] = self.location_site.name
        context['location_site_code'] = self.location_site.site_code
        context['location_site_lat'] = self.location_site.get_centroid().y
        context['location_site_long'] = self.location_site.get_centroid().x
        context['site_id'] = self.location_site.id

        # -- Taxa list
        taxon_group, created = TaxonGroup.objects.get_or_create(
            name=self.taxon_group_name
        )
        self.all_taxa = self.get_all_taxa(taxon_group)

        # Get from same river catchment
        taxa = self.taxa_from_river_catchment()

        if not taxa:
            # Get nearest taxa
            taxa = self.nearest_taxa()

        context['taxa'] = taxa

        context['taxon_rank'] = list(
            rank.name for rank in TaxonomicRank.hierarchy()
        )
        context['reference_category'] = list(
            BiologicalCollectionRecord.objects.filter(
                reference_category__isnull=False).exclude(
                reference_category='').distinct(
                'reference_category').values(
                name=F('reference_category'))
        )
        context['taxon_group_name'] = self.taxon_group_name
        taxon_group = TaxonGroup.objects.filter(
            name=self.taxon_group_name
        )
        context['broad_biotope_list'] = list(
            Biotope.objects.filter(
                taxon_group__in=taxon_group,
                biotope_type=BIOTOPE_TYPE_BROAD
            ).values(
                'id', 'name', 'description', 'display_order'
            ).order_by('display_order')
        )
        context['specific_biotope_list'] = list(
            Biotope.objects.filter(
                taxon_group__in=taxon_group,
                biotope_type=BIOTOPE_TYPE_SPECIFIC
            ).values(
                'id', 'name', 'description', 'display_order'
            ).order_by('display_order')
        )

        context['substratum_list'] = list(
            Biotope.objects.filter(
                taxon_group__in=taxon_group,
                biotope_type=BIOTOPE_TYPE_SUBSTRATUM
            ).values(
                'id', 'name', 'description', 'display_order'
            ).order_by('display_order')
        )

        sampling_method_lower_list = []
        context['sampling_method_list'] = []
        sampling_method_list = list(
            SamplingMethod.objects.filter(
                taxon_group__in=taxon_group
            ).values(
                'id', 'sampling_method'
            ).order_by('order')
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

        return super(CollectionFormView, self).get(request, *args, **kwargs)

    def extra_post(self, post):
        """
        Override this method to process the POST request.
        :param post: POST request
        """
        return

    @method_decorator(login_required)
    def post(self, request, *args, **kwargs):
        date_string = request.POST.get('date', None)
        owner_id = request.POST.get('owner_id', '').strip()
        biotope_id = request.POST.get('biotope', None)
        specific_biotope_id = request.POST.get('specific_biotope', None)
        substratum_id = request.POST.get('substratum', None)
        sampling_method_id = request.POST.get('sampling_method', None)
        abundance_type = request.POST.get('abundance_type', None)
        reference = request.POST.get('study_reference', '')
        reference_category = request.POST.get('reference_category', '')

        biotope = None
        specific_biotope = None
        substratum = None
        sampling_method = None

        if biotope_id:
            biotope = Biotope.objects.get(
                id=biotope_id
            )
        if specific_biotope_id:
            specific_biotope = Biotope.objects.get(
                id=specific_biotope_id
            )
        if substratum_id:
            substratum = Biotope.objects.get(
                id=substratum_id
            )
        if sampling_method_id:
            sampling_method = SamplingMethod.objects.get(
                id=sampling_method_id
            )
        sampling_effort = '{effort} {type}'.format(
            effort=self.request.POST.get('sampling_effort', ''),
            type=self.request.POST.get('sampling_effort_type', '')
        ).strip()

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
        owner = None
        if owner_id:
            try:
                owner = get_user_model().objects.get(
                    id=int(owner_id))
            except get_user_model().DoesNotExist:
                pass
        else:
            owner = self.request.user

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

        # Create a survey
        self.survey = self.create_or_get_survey(collection_date, owner)

        collection_record_ids = []
        for taxon in taxa_id_list:
            observed_key = '{}-observed'.format(taxon)
            abundance_key = '{}-abundance'.format(taxon)
            taxonomy = Taxonomy.objects.get(
                id=taxon
            )
            try:
                if post_data[observed_key] == 'True':
                    abundance = post_data[abundance_key]
                    if abundance:
                        abundance = float(abundance)
                    else:
                        abundance = 0.0
                    collection_record, status = (
                        BiologicalCollectionRecord.objects.get_or_create(
                            collection_date=collection_date,
                            taxonomy=taxonomy,
                            original_species_name=taxonomy.canonical_name,
                            site=self.location_site,
                            collector_user=self.request.user,
                            sampling_method=sampling_method,
                            abundance_number=abundance,
                            owner=owner,
                            biotope=biotope,
                            specific_biotope=specific_biotope,
                            substratum=substratum,
                            reference=reference,
                            reference_category=reference_category,
                            sampling_effort=sampling_effort,
                            abundance_type=abundance_type,
                            survey=self.survey
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
        self.add_last_session(request, session_uuid, {
            'edited_at': int(time.mktime(datetime.now().timetuple())),
            'records': collection_record_ids,
            'location_site': self.location_site.name,
            'form': self.session_identifier
        })
        source_reference_url = (
            '{base_url}?session={session}&identifier={identifier}'.format(
                base_url=reverse('source-reference-form'),
                session=session_uuid,
                identifier=self.session_identifier
            )
        )

        # Create a survey
        abiotic_url = '{base_url}?survey={survey_id}&next={next}'.format(
            base_url=reverse('abiotic-form'),
            survey_id=self.survey.id,
            next=source_reference_url
        )

        self.extra_post(request.POST)

        return HttpResponseRedirect(abiotic_url)


class ModuleFormView(CollectionFormView):

    @method_decorator(login_required)
    def get(self, request, *args, **kwargs):
        module_id = request.GET.get('module', None)
        if not module_id:
            raise Http404('Missing module id')
        try:
            taxon_group = TaxonGroup.objects.get(
                id=module_id
            )
        except TaxonGroup.DoesNotExist:
            raise Http404('Missing module')
        self.taxon_group_name = taxon_group.name
        self.session_identifier = '{}-form'.format(
            taxon_group.name.lower()
        )
        return super(ModuleFormView, self).get(request, *args, **kwargs)


class FishFormView(CollectionFormView):
    session_identifier = 'fish-form'
    taxon_group_name = 'Fish'


class InvertFormView(CollectionFormView):
    session_identifier = 'invert-form'
    taxon_group_name = 'Invertebrates'


class AlgaeFormView(CollectionFormView):
    session_identifier = 'algae-form'
    taxon_group_name = 'Algae'

    def extra_post(self, post):
        """
        Override this method to process the POST request.
        :param post: POST request
        """
        curation_process = post.get('curation_process', None)
        indicator_chl_a = post.get('indicator_chl_a', None)
        indicator_afdm = post.get('indicator_afdm', None)
        ai = post.get('ai', '')
        if not ai:
            ai = None
        algae_data = AlgaeData.objects.filter(
            survey=self.survey
        )
        if algae_data.exists():
            if algae_data.count() > 1:
                algae_data.exclude(id=algae_data[0].id).delete()
        else:
            AlgaeData.objects.create(survey=self.survey)
            algae_data = AlgaeData.objects.filter(survey=self.survey)
        algae_data.update(
            curation_process=curation_process,
            indicator_afdm=indicator_afdm,
            indicator_chl_a=indicator_chl_a,
            ai=ai
        )

        # -- Biomass chemical records
        chem_units = {}
        chl_type = post.get('chl_type', None)
        afdm_type = post.get('afdm_type', None)
        chl_a = post.get('chl_a', None)
        if chl_type and chl_a:
            chem_units[chl_type] = chl_a
        afdm = post.get('afdm', None)
        if afdm_type and afdm:
            chem_units[afdm_type] = afdm
        for chem_unit in chem_units:
            chem = Chem.objects.filter(
                chem_code__iexact=chem_unit
            )
            if chem.exists():
                chem = chem[0]
            else:
                chem = Chem.objects.create(
                    chem_code=chem_unit
                )
            chem_record, _ = ChemicalRecord.objects.get_or_create(
                date=self.survey.date,
                chem=chem,
                location_site=self.survey.site,
                survey=self.survey,
                value=chem_units[chem_unit]
            )
