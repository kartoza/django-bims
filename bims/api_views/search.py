import json
import operator
import hashlib
import ast
from functools import reduce
from django.db.models import Q, Count, F, Value, Case, When
from django.db.models.functions import Concat
from django.contrib.gis.db.models import Union, Extent
from django.contrib.gis.geos import Polygon
from django.contrib.contenttypes.models import ContentType
from rest_framework.response import Response

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
    Survey
)
from bims.tasks.search import search_task
from sass.models import (
    SiteVisitTaxon
)
from bims.utils.search_process import get_or_create_search_process
from bims.utils.api_view import BimsApiView


MAX_PAGINATED_SITES = 20
MAX_PAGINATED_RECORDS = 50


class CollectionSearchAPIView(BimsApiView):
    """
    API View to search collection data
    """

    def get(self, request):
        parameters = request.GET
        search_uri = request.build_absolute_uri()
        search_process, created = get_or_create_search_process(
            search_type=SEARCH_RESULTS,
            query=search_uri
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
            search_task.delay(
                parameters,
                search_process.id,
            )
            result_file = search_process.get_file_if_exits(finished=False)
            if result_file:
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

    def __init__(self, parameters):
        self.parameters = parameters
        super(CollectionSearch, self).__init__()

    def get_request_data(self, field, default_value=None):
        return self.parameters.get(field, default_value)

    def parse_request_json(self, field):
        """
        Parse request json data, from '[23,312]' to array
        :param field: json data
        :return: python object
        """
        json_query = self.get_request_data(field=field)
        if json_query:
            return json.loads(json_query)
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
        return self.get_request_data('search')

    def is_sass_records_only(self):
        """Check if the search only for SASS records"""
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
                'non validated' in validated_values
        ):
            # Get all validated and not validated records
            pass
        elif 'validated' in validated_values:
            additional_filter['validated'] = True
        elif 'non validated' in validated_values:
            additional_filter['validated'] = False

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
    def polygon(self):
        try:
            polygon_coordinates = self.parse_request_json('polygon')
            return Polygon(polygon_coordinates)
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
                    spatial_filter.split(',')[1]
                )
            else:
                if spatial_filter_splitted[0] != 'value':
                    continue
                or_condition |= Q(**{
                    'locationcontext__group__key':
                        spatial_filter_splitted[1],
                    'locationcontext__value': spatial_filter_splitted[2]}
                                  )
            if spatial_filter_groups:
                or_condition |= Q(**{
                    'locationcontext__group__key__in':
                        spatial_filter_groups})
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

    def filter_taxa_records(self, query_dict):
        """
        Filter taxa records
        :param query_dict: dict of query
        """
        if self.filtered_taxa_records is None:
            self.filtered_taxa_records = Taxonomy.objects.filter(
                **query_dict
            )
        else:
            self.filtered_taxa_records = self.filtered_taxa_records.filter(
                **query_dict
            )

    def get_all_taxa_children(self, taxa):
        """
        Get all children from taxa
        :param taxa: QuerySet of taxa
        :return: list all children ids
        """
        query = {}
        parent = ''
        or_condition = Q()
        query['id__in'] = taxa.values_list('id')
        for i in range(6):  # species to class
            parent += 'parent__'
            query[parent + 'in'] = taxa
        for key, value in query.items():
            or_condition |= Q(**{key: value})
        return Taxonomy.objects.filter(or_condition)

    def process_search(self):
        """
        Do the search process.
        :return: search results
        """
        collection_record_model = BiologicalCollectionRecord
        filtered_location_sites = LocationSite.objects.none()

        if self.is_sass_records_only():
            collection_record_model = SiteVisitTaxon
        rank = self.get_request_data('rank')
        bio = None
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
        elif self.search_query and bio is None:
            bio = collection_record_model.objects.filter(
                original_species_name__icontains=self.search_query
            )
            if not bio.exists():
                bio = collection_record_model.objects.filter(
                    taxonomy__scientific_name__icontains=self.search_query
                )
            if not bio.exists():
                bio = collection_record_model.objects.filter(
                    site__site_code__icontains=self.search_query
                )
            if not bio.exists():
                bio = collection_record_model.objects.filter(
                    site__river__name__icontains=self.search_query
                )
            if not bio.exists():
                # Search by vernacular names
                bio = collection_record_model.objects.filter(
                    taxonomy__vernacular_names__name__icontains=
                    self.search_query
                )
        if bio is None:
            bio = collection_record_model.objects.all()

        filters = dict()
        validation_filter = self.validation_filter()
        if validation_filter:
            filters.update(validation_filter)

        source_collection_filters = []

        filters['taxonomy__isnull'] = False
        if self.site_ids:
            filters['site__in'] = self.site_ids
        if self.categories:
            self.filter_taxa_records(
                {
                    'origin__in': self.categories
                }
            )
        if self.year_ranges:
            filters['collection_date__range'] = self.year_ranges
        if self.months:
            filters['collection_date__month__in'] = self.months
        if self.reference:
            filters['source_reference__in'] = self.reference
        if self.conservation_status:
            self.filter_taxa_records(
                {
                    'iucn_status__category__in':
                        self.conservation_status
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
                }
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

        bio = bio.filter(**filters)

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

        if self.collector:
            collectors = Profile.objects.annotate(
                full_name=Concat('first_name', Value(' '), 'last_name')
            ).filter(full_name__in=self.collector)
            collector_list = list(collectors.values_list('id', flat=True))
            bio = bio.filter(
                Q(survey__owner__in=collector_list) |
                Q(sitevisittaxon__site_visit__owner__in=collector_list)
            )

        if self.collectors:
            bio = bio.filter(
                Q(survey__owner__in=self.collectors) |
                Q(sitevisittaxon__site_visit__owner__in=self.collectors)
            )

        if self.reference_category:
            clauses = (
                Q(source_reference__polymorphic_ctype=
                  ContentType.objects.get_for_model(
                      LIST_SOURCE_REFERENCES[p])) for p in
                self.reference_category
            )
            reference_category_filter = reduce(operator.or_, clauses)
            bio = bio.filter(reference_category_filter)

        spatial_filters = self.spatial_filter
        if spatial_filters:
            if not filtered_location_sites:
                filtered_location_sites = LocationSite.objects.filter(
                    spatial_filters
                )
            else:
                filtered_location_sites = filtered_location_sites.filter(
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

        if self.modules:
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
                    module_group__id=self.modules[0]
                )

        if self.get_request_data('polygon'):
            if not filtered_location_sites:
                filtered_location_sites = LocationSite.objects.filter(
                    geometry_point__within=self.polygon
                )
            else:
                filtered_location_sites = filtered_location_sites.filter(
                    geometry_point__within=self.polygon
                )

        if self.abiotic_data:
            if not filtered_location_sites:
                filtered_location_sites = LocationSite.objects.filter(
                    Q(survey__chemical_collection_record__isnull=False) |
                    Q(chemical_collection_record__isnull=False)
                )
            else:
                filtered_location_sites = filtered_location_sites.filter(
                    Q(survey__chemical_collection_record__isnull=False) |
                    Q(chemical_collection_record__isnull=False)
                )

        if filtered_location_sites.exists():
            bio = bio.filter(
                site__in=filtered_location_sites
            ).select_related()

        if bio.exists():
            self.location_sites_raw_query = LocationSite.objects.filter(
                id__in=bio.values('site_id')
            ).annotate(site_id=F('id')).values(
                'site_id',
                'geometry_point',
                'name'
            ).query.sql_with_params()

        self.collection_records = bio
        return self.collection_records

    def get_summary_data(self):
        if not self.collection_records:
            self.process_search()

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

        return {
            'total_records': self.collection_records.count(),
            'total_sites': sites.count(),
            'total_survey': survey.count(),
            'records': list(collections),
            'sites': list(sites)
        }
