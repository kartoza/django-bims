import datetime
import json
import time
import urllib.parse
import operator
import hashlib
import ast
import logging
from functools import reduce

from preferences import preferences

from bims.models.chemical_record import ChemicalRecord

from bims.models.water_temperature import WaterTemperature
from django.db.models import Q, Count, F, Value, Case, When, IntegerField
from django.db.models.functions import Concat
from django.db.models.query import QuerySet
from django.contrib.gis.db.models import Union, Extent
from django.contrib.gis.geos import Polygon, GEOSGeometry
from django.contrib.contenttypes.models import ContentType
from rest_framework.response import Response

from bims.serializers.boundary_serializer import check_crs
from geonode.people.models import Profile
from bims.models import (
    BiologicalCollectionRecord,
    Boundary,
    UserBoundary,
    SEARCH_RESULTS,
    SEARCH_PROCESSING,
    Taxonomy,
    Endemism,
    LIST_SOURCE_REFERENCES,
    LocationSite,
    Survey,
    TaxonGroup
)
from bims.tasks.search import search_task
from sass.models import (
    SiteVisitTaxon
)
from bims.utils.search_process import get_or_create_search_process
from bims.utils.api_view import BimsApiView

logger = logging.getLogger('bims')

MAX_PAGINATED_SITES = 20
MAX_PAGINATED_RECORDS = 50


class CollectionSearchAPIView(BimsApiView):
    """
    API View to search collection data
    """

    def get(self, request):
        parameters = request.GET.dict()
        search_uri = request.build_absolute_uri()
        search_process, created = get_or_create_search_process(
            search_type=SEARCH_RESULTS,
            query=search_uri,
        )

        if self.is_cached():
            results = search_process.get_file_if_exits()
            if results:
                results['process_id'] = search_process.process_id
                if 'sites' in results:
                    results['total_unique_sites'] = len(results['sites'])
                    results['sites'] = results['sites'][:MAX_PAGINATED_SITES]
                if 'records' in results:
                    results['total_unique_taxa'] = len(results['records'])
                    results['records'] = (
                        results['records'][:MAX_PAGINATED_RECORDS]
                    )
                results['sites_raw_query'] = search_process.process_id
                return Response(results)

        # Create process id
        data_for_process_id = dict()
        data_for_process_id['search_uri'] = search_uri
        data_for_process_id['requester_id'] = request.user.id if not request.user.is_anonymous else 0
        data_for_process_id['collections_total'] = (
            BiologicalCollectionRecord.objects.all().count()
        )
        # Generate unique process id by search uri and total of collections
        process_id = hashlib.sha256(
            str(json.dumps(data_for_process_id, sort_keys=True)
                ).encode('utf-8')
        ).hexdigest()
        search_process.set_process_id(process_id)
        search_process.set_status(SEARCH_PROCESSING)

        if self.is_background_request():
            # call worker task
            task = search_task.delay(
                parameters,
                search_process.id,
            )
            result_file = search_process.get_file_if_exits(finished=False)
            if result_file:
                result_file['task_id'] = task.id
                return Response(result_file)
            return Response({'status': 'result/status not exists'})
        else:
            search_results = search_task(
                parameters,
                search_process.id,
                self.is_background_request()
            )
            return Response(search_results)


class CollectionSearch(object):
    location_sites_raw_query = ''
    collection_records = None
    filtered_taxa_records = None
    sass_only = False
    site = None
    taxon_groups = TaxonGroup.objects.all()
    start_time = None

    def __init__(self, parameters):
        self.parameters = parameters
        super(CollectionSearch, self).__init__()

    def get_request_data(self, field, default_value=None):
        request_data = self.parameters.get(field, default_value)
        if isinstance(request_data, list):
            request_data = request_data[0]
        return request_data

    def parse_request_json(self, field):
        """
        Parse request json data, from '[23,312]' to array
        :param field: json data
        :return: python object
        """
        json_query = self.get_request_data(field=field)
        if json_query:
            try:
                return json.loads(json_query)
            except json.decoder.JSONDecodeError:
                return json.loads(
                    urllib.parse.unquote(json_query)
                )
        else:
            return None

    def extent(self):
        # Get extent from collection results
        if self.collection_records.count() < 1:
            return []
        extent = LocationSite.objects.filter(
            id__in=self.collection_records.values('site')
        ).aggregate(extent=Extent('geometry_point'))
        return list(extent['extent'])

    @property
    def site_ids(self):
        site_ids = self.get_request_data('siteId')
        if site_ids:
            return site_ids.split(',')
        else:
            return None

    @property
    def search_query(self):
        search_query_value = self.get_request_data('search')
        return search_query_value if search_query_value else ''

    def is_sass_records_only(self):
        """Check if the search only for SASS records"""
        if self.sass_only:
            return True
        if self.ecological_category:
            return True
        validated_values = self.parse_request_json('validated')
        if validated_values:
            if (
                'sass accredited' in validated_values or
                'non sass accredited' in validated_values
            ):
                return True
        return False

    def validation_filter(self):
        """
        Get validation filter
        :return: dict of validation filter
        """
        validated_values = self.parse_request_json('validated')
        additional_filter = {}
        if not validated_values:
            return {}
        if (
                'validated' in validated_values and
                'unvalidated' in validated_values
        ):
            # Get all validated and not validated records
            pass
        elif 'validated' in validated_values:
            additional_filter['survey__validated'] = True
        elif 'unvalidated' in validated_values:
            additional_filter['survey__validated'] = False
        elif 'in review' in validated_values:
            additional_filter['survey__ready_for_validation'] = True

        return additional_filter

    @property
    def taxon_id(self):
        taxon_id_query = self.get_request_data('taxon')
        if taxon_id_query:
            return taxon_id_query.split(',')
        else:
            return None

    @property
    def year_ranges(self):
        year_from = self.get_request_data('yearFrom')
        year_to = self.get_request_data('yearTo')
        if year_from and year_to:
            return [year_from + '-01-01', year_to + '-12-31']
        return None

    @property
    def months(self):
        month_query = self.get_request_data('months')
        if month_query:
            return month_query.split(',')
        else:
            return None

    def invasions(self):
        return self.parse_request_json('invasions')

    @property
    def reference_category(self):
        return self.parse_request_json('referenceCategory')

    @property
    def categories(self):
        categories = self.parse_request_json('category')
        # Add invasive alien
        if categories and 'alien' in categories:
            categories.append('alien-non-invasive')
            categories.append('alien-invasive')
            if 'non-native' not in categories:
                categories.append('non-native')
        return categories

    @property
    def collector(self):
        return self.parse_request_json('collector')

    @property
    def reference(self):
        return self.parse_request_json('reference')

    @property
    def conservation_status(self):
        return self.parse_request_json('conservationStatus')

    @property
    def decision_support_tools(self):
        return self.parse_request_json('dst')

    @property
    def boundary(self):
        return self.parse_request_json('boundary')

    @property
    def user_boundary(self):
        return self.parse_request_json('userBoundary')

    @property
    def endemic(self):
        return self.parse_request_json('endemic')

    @property
    def source_collection(self):
        return self.parse_request_json('sourceCollection')

    @property
    def ecological_category(self):
        return self.parse_request_json('ecologicalCategory')

    @property
    def collectors(self):
        return self.parse_request_json('collectors')

    @property
    def in_review(self):
        _in_review = self.get_request_data('inReview')
        if _in_review:
            try:
                return ast.literal_eval(_in_review)
            except ValueError:
                return False
        else:
            return False

    @property
    def polygon(self):
        try:
            layer_param = self.parse_request_json('polygon')
            if isinstance(layer_param, int):
                try:
                    user_boundary = UserBoundary.objects.get(
                        id=layer_param
                    )
                    crs = check_crs(user_boundary)
                    if '3857' in crs:
                        geometry = GEOSGeometry(
                            str(user_boundary.geometry).replace(
                                '4326',  '3857'))
                        geometry.transform(4326)
                    else:
                        geometry = user_boundary.geometry
                    return geometry
                except UserBoundary.DoesNotExist:
                    return None
            return Polygon(layer_param)
        except TypeError:
            return None

    @property
    def abiotic_data(self):
        _abiotic_data = self.get_request_data('abioticData')
        if _abiotic_data:
            try:
                return ast.literal_eval(_abiotic_data)
            except ValueError:
                return False
        else:
            return False

    @property
    def modules(self):
        modules_query = self.get_request_data('modules')
        if modules_query:
            return modules_query.split(',')
        else:
            return None

    @property
    def ecosystem_type(self):
        ecosystem_type = self.get_request_data('ecosystemType')
        if ecosystem_type:
            ecosystem_types = ecosystem_type.split(',')
            if 'Unspecified' in ecosystem_types:
                ecosystem_types = (
                    list(map(
                        lambda x: x.replace('Unspecified', ''), ecosystem_types))
                )
            return ecosystem_types
        else:
            return []

    @property
    def spatial_filter(self):
        spatial_filters = self.parse_request_json('spatialFilter')
        spatial_filter_groups = []
        or_condition = Q()
        if not spatial_filters:
            return []
        for spatial_filter in spatial_filters:
            spatial_filter_splitted = spatial_filter.split(',')
            if 'group' in spatial_filter_splitted:
                spatial_filter_groups.append(
                    ','.join(spatial_filter.split(',')[1:])
                )
            else:
                if spatial_filter_splitted[0] != 'value':
                    continue
                or_condition |= Q(**{
                    'locationcontext__group__key':
                        spatial_filter_splitted[1],
                    'locationcontext__value': ','.join(
                        spatial_filter_splitted[2:])})
        if spatial_filter_groups:
            or_condition |= Q(**{
                'locationcontext__group__key__in':
                    spatial_filter_groups})
            or_condition &= ~Q(**{
                'locationcontext__value': 'None'
            })
            or_condition &= ~Q(**{
                'locationcontext__value': ''
            })
        return or_condition

    @property
    def spatial_filter_group_query(self):
        spatial_filters = self.parse_request_json('spatialFilter')
        spatial_filter_group_ids = []
        if not spatial_filters:
            return []
        for spatial_filter in spatial_filters:
            if 'group-' in spatial_filter:
                spatial_filter = spatial_filter.replace(
                    'group-', ''
                )
                spatial_filter_group_ids.append(spatial_filter)
        return spatial_filter_group_ids

    @property
    def thermal_module(self):
        thermal_module = self.get_request_data('thermalModule')
        if thermal_module:
            try:
                return ast.literal_eval(thermal_module)
            except ValueError:
                return False
        else:
            return False

    def filter_taxa_records(self, query_dict, select_related=None):
        """
        Filter taxa records
        :param query_dict: dict of query
        """
        if self.filtered_taxa_records is None:
            taxa = Taxonomy.objects
            if select_related:
                taxa = taxa.select_related(select_related)
            self.filtered_taxa_records = taxa.filter(
                **query_dict
            )
        else:
            if select_related:
                self.filtered_taxa_records = self.filtered_taxa_records.select_related(
                    select_related
                )
            self.filtered_taxa_records = self.filtered_taxa_records.filter(
                **query_dict
            )

    def process_search(self):
        """
        Do the search process.
        :return: search results
        """
        self.start_time = time.time()
        collection_record_model = BiologicalCollectionRecord
        filtered_location_sites = None
        bio_filtered = False

        if self.is_sass_records_only():
            collection_record_model = SiteVisitTaxon

        rank = self.get_request_data('rank')
        bio = None

        collection_records_by_site = collection_record_model.objects.all()

        if rank:
            taxa_list = []
            taxa_children_exist = True
            taxa = Taxonomy.objects.filter(
                scientific_name__icontains=self.search_query
            ).distinct('id')
            while taxa_children_exist:
                taxa_list.extend(list(taxa.values_list('id', flat=True)))
                taxa = Taxonomy.objects.filter(
                    parent__in=taxa,
                ).distinct('id')
                if not taxa:
                    taxa_children_exist = False
            self.filter_taxa_records({
                'id__in': taxa_list,
                'biologicalcollectionrecord__isnull': False
            })
        elif self.search_query:
            bio = collection_records_by_site.filter(
                Q(taxonomy__canonical_name__icontains=self.search_query) |
                Q(taxonomy__accepted_taxonomy__canonical_name__icontains=
                  self.search_query) |
                Q(taxonomy__synonym__canonical_name__icontains=
                  self.search_query)
            )
            if not bio.exists():
                bio = collection_records_by_site.filter(
                    original_species_name__icontains=self.search_query
                )
            if not bio.exists():
                bio = collection_records_by_site.filter(
                    taxonomy__scientific_name__icontains=self.search_query
                )
            if not bio.exists():
                bio = collection_records_by_site.filter(
                    site__site_code__icontains=self.search_query
                )
            if not bio.exists():
                bio = collection_records_by_site.filter(
                    site__legacy_river_name__icontains=self.search_query
                )
            if not bio.exists():
                bio = collection_records_by_site.filter(
                    site__river__name__icontains=self.search_query
                )
            if not bio.exists():
                # Search by vernacular names
                bio = collection_records_by_site.filter(
                    taxonomy__vernacular_names__name__icontains=
                    self.search_query
                )
        if bio is None:
            bio = collection_records_by_site
        else:
            bio_filtered = True

        filters = dict()
        validation_filter = self.validation_filter()
        if validation_filter:
            filters.update(validation_filter)

        if self.in_review:
            filters.update({
                'survey__ready_for_validation': True
            })

        source_collection_filters = []

        if self.site_ids:
            filters['site__in'] = self.site_ids
        invasions = self.invasions()
        if invasions:
            self.filter_taxa_records({
                'invasion__id__in': invasions
            }, 'invasion')
        if self.categories:
            self.filter_taxa_records(
                {
                    'origin__in': self.categories
                }
            )
        if self.decision_support_tools:
            filters['decisionsupporttool__dst_name__name__in'] = (
                self.decision_support_tools
            )
        if self.year_ranges:
            filters['survey__date__range'] = self.year_ranges
        if self.months:
            filters['survey__date__month__in'] = self.months
        if self.reference:
            filters['source_reference__in'] = self.reference

        all_conservation_status = self.conservation_status
        if all_conservation_status:
            global_conservation_status = (
                [status
                for status in all_conservation_status
                if 'N__' not in status]
            )
            national_conservation_status = (
                [status.replace('N__', '')
                 for status in all_conservation_status
                 if 'N__' in status]
            )
            if global_conservation_status:
                self.filter_taxa_records(
                    {
                        'iucn_status__category__in':
                            global_conservation_status,
                    }
                )
            if national_conservation_status:
                self.filter_taxa_records(
                    {
                        'national_conservation_status__category__in':
                            national_conservation_status,
                    }
                )
        if self.source_collection:
            for source_collection in self.source_collection:
                if source_collection not in source_collection_filters:
                    source_collection_filters.append(source_collection)
        if source_collection_filters:
            filters['source_collection__in'] = source_collection_filters
        if self.endemic:
            endemism_list = []
            for endemic in self.endemic:
                endemism_list.extend(list(
                    Endemism.objects.filter(
                        name__icontains=endemic
                    ).values_list('id', flat=True)
                ))
            endemism_list = list(set(endemism_list))
            self.filter_taxa_records(
                {
                    'endemism__in': endemism_list
                },
                'endemism'
            )
        if self.taxon_id:
            self.filter_taxa_records({
                'id__in': self.taxon_id
            })
        if self.boundary:
            boundary = Boundary.objects.filter(id__in=self.boundary)
            if len(boundary) == 0:
                geometry_found = True
            else:
                geometry_found = boundary[0].geometry
            while not geometry_found:
                boundary = Boundary.objects.filter(
                    top_level_boundary__in=boundary
                )
                if len(boundary) == 0:
                    break
                geometry_found = boundary[0].geometry
            if geometry_found:
                filters['site__boundary__in'] = boundary
        if self.ecological_category:
            (
                filters[
                    'site_visit__'
                    'sitevisitecologicalcondition__'
                    'ecological_condition__category__in']
            ) = self.ecological_category

        if self.filtered_taxa_records is not None:
            filters['taxonomy__in'] = self.filtered_taxa_records
            bio = bio.select_related('taxonomy')

        if filters:
            filters['taxonomy__isnull'] = False
            bio_filtered = True

        bio = bio.filter(**filters)

        requester_id = self.parameters.get('requester', None)

        bio = bio.filter(
            Q(owner_id=requester_id) |
            Q(
                Q(end_embargo_date__lte=datetime.date.today()) |
                Q(end_embargo_date__isnull=True)
            )
        )

        # Filter collection record with SASS Accreditation status
        validated_values = self.parse_request_json('validated')
        if validated_values:
            if (
                'sass accredited' in validated_values and
                'non sass accredited' in validated_values
            ):
                pass
            elif 'sass accredited' in validated_values:
                bio = bio.filter(
                    owner__bims_profile__sass_accredited_date_from__isnull
                    =False,
                    owner__bims_profile__sass_accredited_date_to__isnull
                    =False,
                    collection_date__gte=F(
                        'owner__bims_profile__sass_accredited_date_from'),
                    collection_date__lte=F(
                        'owner__bims_profile__sass_accredited_date_to')
                )
                bio_filtered = True
            elif 'non sass accredited' in validated_values:
                bio = bio.filter(
                    Q(
                        owner__bims_profile__sass_accredited_date_from__isnull
                        =True) |
                    Q(
                        owner__bims_profile__sass_accredited_date_to__isnull
                        =True) |
                    Q(collection_date__lte=F(
                        'owner__bims_profile__sass_accredited_date_from')) |
                    Q(collection_date__gte=F(
                        'owner__bims_profile__sass_accredited_date_to'))
                )
                bio_filtered = True

        if self.collector:
            collectors = Profile.objects.annotate(
                full_name=Concat('first_name', Value(' '), 'last_name')
            ).filter(full_name__in=self.collector)
            collector_list = list(collectors.values_list('id', flat=True))
            bio = bio.filter(
                Q(survey__owner__in=collector_list)
            )
            bio_filtered = True

        if self.collectors:
            bio = bio.filter(
                Q(survey__owner__in=self.collectors)
            )
            bio_filtered = True

        if self.reference_category:
            clauses = (
                Q(source_reference__polymorphic_ctype=
                  ContentType.objects.get_for_model(
                      LIST_SOURCE_REFERENCES[p])) for p in
                self.reference_category
            )
            reference_category_filter = reduce(operator.or_, clauses)
            bio = bio.filter(reference_category_filter)
            bio_filtered = True

        if preferences.SiteSetting.enable_ecosystem_type and self.parameters.get('ecosystemType'):
            ecosystem_types = self.ecosystem_type
            if ecosystem_types:
                if not isinstance(filtered_location_sites, QuerySet):
                    filtered_location_sites = LocationSite.objects.filter(
                        ecosystem_type__in=ecosystem_types
                    )
                else:
                    filtered_location_sites = filtered_location_sites.filter(
                        ecosystem_type__in=ecosystem_types
                    )
            else:
                filtered_location_sites = LocationSite.objects.none()

        spatial_filters = self.spatial_filter
        if spatial_filters:
            if not isinstance(filtered_location_sites, QuerySet):
                filtered_location_sites = LocationSite.objects.select_related(
                    'locationcontextgroup'
                ).filter(
                    spatial_filters
                )
            else:
                filtered_location_sites = filtered_location_sites.select_related(
                    'locationcontextgroup'
                ).filter(
                    spatial_filters
                )

        if self.user_boundary:
            user_boundaries = UserBoundary.objects.filter(
                pk__in=self.user_boundary
            )
            if user_boundaries:
                bio = bio.filter(site__geometry_point__intersects=(
                    user_boundaries.aggregate(area=Union('geometry'))['area']
                ))
                bio_filtered = True

        if self.modules:
            # For Intersection methods :
            if len(self.modules) > 1:
                module_filter = []
                for taxon_group in self.modules:
                    module_filter.append(
                        bio.filter(
                            module_group__id=taxon_group
                        ).values_list('site_id'))
                intersections = module_filter[0].intersection(
                    *module_filter[1:]
                )
                bio = bio.filter(site_id__in=intersections)
            else:
                bio = bio.filter(
                    module_group__id__in=self.modules
                )
            bio_filtered = True

        if self.get_request_data('polygon'):
            polygon = self.polygon
            if polygon:
                if not isinstance(filtered_location_sites, QuerySet):
                    filtered_location_sites = LocationSite.objects.filter(
                        geometry_point__within=polygon
                    )
                    bio = bio.filter(
                        site__in=filtered_location_sites
                    )
                    bio_filtered = True
                else:
                    filtered_location_sites = filtered_location_sites.filter(
                        geometry_point__within=polygon
                    )

        if self.abiotic_data:
            if not isinstance(filtered_location_sites, QuerySet):
                filtered_location_sites = LocationSite.objects.all()

            filtered_location_sites = filtered_location_sites.filter(
                survey__chemical_collection_record__isnull=False
            )

        if (
            isinstance(filtered_location_sites, QuerySet) and
            filtered_location_sites.count() > 0
        ):
            bio = bio.filter(
                site__in=filtered_location_sites
            ).select_related()
            bio_filtered = True

        water_temperature = []

        if not bio_filtered:
            bio = collection_record_model.objects.none()

        if self.thermal_module:
            water_temperature = list(WaterTemperature.objects.all().order_by(
                'location_site').distinct('location_site').values_list(
                'location_site', flat=True))
            if not isinstance(filtered_location_sites, QuerySet):
                filtered_location_sites = LocationSite.objects.filter(
                    id__in=water_temperature
                )
            else:
                filtered_location_sites = filtered_location_sites.filter(
                    id__in=water_temperature
                )
            if bio_filtered:
                bio = bio.filter(
                    site__in=filtered_location_sites
                ).select_related()

        if bio.exists() or water_temperature:
            location_sites_filter = LocationSite.objects.filter(
                Q(id__in=bio.values('site_id')) |
                Q(id__in=water_temperature)
            )
            if self.search_query and LocationSite.objects.filter(
                site_code__icontains=self.search_query
            ).exists():
                location_sites_filter = LocationSite.objects.filter(
                    Q(id__in=bio.values('site_id')) |
                    Q(id__in=water_temperature) |
                    Q(site_code__icontains=self.search_query)
                )

                location_sites_filter = location_sites_filter.filter(
                    Q(owner_id=requester_id) |
                    Q(
                        Q(end_embargo_date__lte=datetime.date.today()) |
                        Q(end_embargo_date__isnull=True)
                    )
                )

                if preferences.SiteSetting.enable_ecosystem_type and self.ecosystem_type:
                    location_sites_filter = location_sites_filter.filter(
                        ecosystem_type__in=self.ecosystem_type
                    )
            self.location_sites_raw_query = location_sites_filter.annotate(
                site_id=F('id')).values(
                'site_id',
                'geometry_point',
                'name',
                'ecosystem_type'
            ).query.sql_with_params()

        if not self.location_sites_raw_query and self.search_query:
            self.location_sites_raw_query = LocationSite.objects.filter(
                Q(owner_id=requester_id) |
                Q(
                    Q(end_embargo_date__lte=datetime.date.today()) |
                    Q(end_embargo_date__isnull=True)
                ),
                site_code__icontains=self.search_query
            ).annotate(site_id=F('id')).values(
                'site_id',
                'geometry_point',
                'name',
                'ecosystem_type'
            ).query.sql_with_params()

        self.collection_records = bio
        return self.collection_records

    def search_sites_with_abiotic(self, site_ids: list):
        if not site_ids:
            site_ids = []
        else:
            site_ids = [ site['site_id'] for site in site_ids ]
        collector_list = []
        if self.collector:
            collectors = Profile.objects.annotate(
                full_name=Concat('first_name', Value(' '), 'last_name')
            ).filter(full_name__in=self.collector)
            collector_list = list(collectors.values_list('id', flat=True))
        source_reference = self.reference
        if not source_reference:
            source_reference = []
        chemical_record_sites = ChemicalRecord.objects.filter(
            Q(survey__owner__in=collector_list) |
            Q(source_reference__in=source_reference)
        ).exclude(
            survey__site__in=site_ids
        ).annotate(
            name=Case(
                When(survey__site__site_code='',
                     then=F('survey__site__name')),
                default=F('survey__site__site_code')
            ),
            site_id=F('survey__site__id')
        ).values(
            'site_id', 'name'
        ).annotate(
            total_abiotic_data=Count('survey__site'),
            total_survey=Count('survey', distinct=True)
        ).distinct()
        return chemical_record_sites

    def get_summary_data(self):
        if not self.collection_records:
            self.process_search()
        else:
            self.start_time = time.time()

        # Get order_by
        order_by = self.get_request_data('orderBy', 'name')
        valid_order = [
            'total', '-total', 'name', '-name', 'total_survey', '-total_survey'
        ]
        if order_by not in valid_order:
            order_by = 'name'

        # Survey
        survey = (
            Survey.objects.filter(
                id__in=self.collection_records.values('survey')
            )
        )

        collections = (
            self.collection_records.annotate(
                name=F('taxonomy__canonical_name'),
                taxon_id=F('taxonomy_id')
            ).values(
                'taxon_id', 'name'
            ).annotate(
                total=Count('taxonomy'),
                total_survey=Count('survey', distinct=True)
            ).order_by(order_by)
        )

        sites = (
            self.collection_records.annotate(
                name=Case(
                    When(site__site_code='',
                         then=F('site__name')),
                    default=F('site__site_code')
                )
            ).values(
                'site_id', 'name'
            ).annotate(
                total=Count('site'),
                total_survey=Count('survey', distinct=True)
            ).order_by(order_by)
        )

        # Search for sites without any occurrences
        if (
                self.search_query and
                LocationSite.objects.filter(
                    site_code__icontains=self.search_query).exists()
        ):
            sites_without_occurrences = LocationSite.objects.exclude(
                id__in=sites.values('site_id')
            ).filter(
                site_code__icontains=self.search_query,
                ecosystem_type__in=self.ecosystem_type
            ).extra(
                select={
                    'name': 'site_code'
                }
            ).annotate(
                site_id=F('id')
            ).values(
                'site_id', 'name'
            ).annotate(
                total=Value(0, output_field=IntegerField()),
                total_survey=Count('survey', distinct=True)
            ).order_by(order_by)
        else:
            sites_without_occurrences = LocationSite.objects.none()

        thermal_sites = WaterTemperature.objects.none()
        if self.thermal_module:
            thermal_sites = WaterTemperature.objects.exclude(
                location_site_id__in=list(sites.values_list('site_id'))
            ).annotate(
                name=Case(
                    When(location_site__site_code='',
                         then=F('location_site__name')),
                    default=F('location_site__site_code')
                ),
                site_id=F('location_site_id')
            ).values(
                'site_id', 'name'
            ).annotate(
                total_thermal=Count('location_site')
            ).order_by(order_by).distinct()

        site_list = list(sites) + list(sites_without_occurrences)

        abiotic_sites = []
        if self.abiotic_data:
            abiotic_sites = self.search_sites_with_abiotic(site_list)

        for thermal_site in thermal_sites:
            site_list.append({
                'site_id': thermal_site['site_id'],
                'name': thermal_site['name'],
                'total': 0,
                'total_survey': 0,
                'total_water_temperature_data': thermal_site['total_thermal']
            })

        for abiotic_site in abiotic_sites:
            if not abiotic_site['site_id']:
                continue
            site_list.append({
                'site_id': abiotic_site['site_id'],
                'name': abiotic_site['name'],
                'total': 0,
                'total_survey': abiotic_site['total_survey'],
                'total_abiotic_data': abiotic_site['total_abiotic_data']
            })

        return {
            'duration': time.time() - self.start_time if self.start_time else 0,
            'total_records': self.collection_records.count(),
            'total_sites': (
                sites.count() + (thermal_sites.count() if thermal_sites else 0) +
                sites_without_occurrences.count() + len(abiotic_sites)
            ),
            'total_survey': survey.count(),
            'records': list(collections),
            'sites': site_list
        }
