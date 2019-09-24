from datetime import date
import json
import operator
import hashlib
from django.db.models import Q, Count, F, Value
from django.db.models.functions import Concat
from django.contrib.gis.db.models import Union, Extent
from django.contrib.contenttypes.models import ContentType
from rest_framework.response import Response

from geonode.people.models import Profile
from bims.models import (
    BiologicalCollectionRecord,
    Boundary,
    UserBoundary,
    SEARCH_RESULTS,
    SEARCH_PROCESSING,
    TaxonGroup,
    Taxonomy,
    Endemism,
    LIST_SOURCE_REFERENCES,
)
from bims.tasks.search import search_task
from sass.models import (
    SiteVisitTaxon
)
from bims.utils.search_process import get_or_create_search_process
from bims.utils.api_view import BimsApiView


MAX_PAGINATED_SITES = 20


class SearchAPIView(BimsApiView):
    """
    Search with django query
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
                results['sites_raw_query'] = search_process.process_id
                return Response(results)

        # Create process id
        data_for_process_id = dict()
        data_for_process_id['search_uri'] = search_uri
        data_for_process_id['collections_total'] = (
            BiologicalCollectionRecord.objects.all().count()
        )
        # Generate unique process id by search uri and total of collections
        process_id = hashlib.md5(
            json.dumps(data_for_process_id, sort_keys=True)
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


class Search(object):
    location_sites_raw_query = ''
    collection_records = None

    def __init__(self, parameters):
        self.parameters = parameters
        super(Search, self).__init__()

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
        if not self.collection_records:
            return []
        extent = self.collection_records.aggregate(
            extent=Extent('site__geometry_point')
        )
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

        if (
            'sass accredited' in validated_values and
            'non sass accredited' in validated_values
        ):
            pass
        elif 'sass accredited' in validated_values:
            additional_filter[
                'owner__bims_profile__sass_accredited_date_to__gte'] = (
                date.today()
            )
        elif 'non sass accredited' in validated_values:
            additional_filter[
                'owner__bims_profile__sass_accredited_date_to__lte'] = (
                date.today()
            )

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
        return self.parse_request_json('category')

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
                    'site__locationcontext__key': spatial_filter_splitted[1],
                    'site__locationcontext__value': spatial_filter_splitted[2]}
                                  )
            if spatial_filter_groups:
                or_condition |= Q(**{
                    'site__locationcontext__key__in':
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

        if self.ecological_category:
            collection_record_model = SiteVisitTaxon

        if self.search_query:
            bio = collection_record_model.objects.filter(
                Q(original_species_name__icontains=self.search_query) |
                Q(taxonomy__scientific_name__icontains=self.search_query) |
                Q(site__site_code__icontains=self.search_query) |
                Q(site__river__name__icontains=self.search_query)
            )
            if not bio:
                # Search by vernacular names
                bio = collection_record_model.objects.filter(
                    taxonomy__vernacular_names__name__icontains=
                    self.search_query
                )
        else:
            bio = collection_record_model.objects.all()

        filters = dict()
        validation_filter = self.validation_filter()
        if validation_filter:
            filters.update(validation_filter)

        filters['taxonomy__isnull'] = False
        if self.site_ids:
            filters['site__in'] = self.site_ids
        if self.categories:
            filters['category__in'] = self.categories
        if self.year_ranges:
            filters['collection_date__range'] = self.year_ranges
        if self.months:
            filters['collection_date__month__in'] = self.months
        if self.reference:
            filters['source_reference__in'] = self.reference
        if self.conservation_status:
            filters['taxonomy__iucn_status__category__in'] = (
                self.conservation_status
            )
        if self.source_collection:
            filters['source_collection__in'] = self.source_collection
        if self.endemic:
            endemism_list = []
            for endemic in self.endemic:
                endemism_list.extend(list(
                    Endemism.objects.filter(
                        name__icontains=endemic
                    ).values_list('id', flat=True)
                ))
            endemism_list = list(set(endemism_list))
            filters['taxonomy__endemism__in'] = endemism_list
        if self.taxon_id:
            filters['taxonomy__in'] = self.taxon_id
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
        bio = bio.filter(**filters)

        if self.collector:
            sass_owners = Profile.objects.annotate(
                full_name=Concat('first_name', Value(' '), 'last_name')
            ).filter(full_name__in=self.collector)
            bio = bio.filter(
                Q(collector__in=self.collector) |
                Q(sitevisittaxon__site_visit__owner__in=list(
                    sass_owners.values_list('id', flat=True)))
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

        _spatial_fitler = self.spatial_filter
        if _spatial_fitler:
            bio = bio.filter(_spatial_fitler)

        if self.user_boundary:
            user_boundaries = UserBoundary.objects.filter(
                pk__in=self.user_boundary
            )
            if user_boundaries:
                bio = bio.filter(site__geometry_point__intersects=(
                    user_boundaries.aggregate(area=Union('geometry'))['area']
                ))

        if self.modules:
            taxon_groups = TaxonGroup.objects.filter(
                pk__in=self.modules
            )
            all_parent_taxa = list(
                taxon_groups.values_list('taxonomies', flat=True))
            group_source_collections = list(
                taxon_groups.values_list('source_collection', flat=True)
            )
            parent = 'taxonomy__'
            module_query = {}
            module_or_condition = Q()
            module_query['taxonomy__id__in'] = all_parent_taxa
            for i in range(6):  # species to class
                parent += 'parent__'
                module_query[parent + 'in'] = all_parent_taxa
            for key, value in module_query.items():
                module_or_condition |= Q(**{key: value})
            module_or_condition |= Q(
                source_collection__in=group_source_collections)
            if module_or_condition:
                bio = bio.filter(module_or_condition)

        self.location_sites_raw_query = bio.distinct('site').values(
            'site_id',
            'site__geometry_point',
            'site__name').query.sql_with_params()

        self.collection_records = bio
        return self.collection_records

    def get_summary_data(self):
        if not self.collection_records:
            self.process_search()

        collections = (
            self.collection_records.annotate(
                name=F('taxonomy__canonical_name'),
                taxon_id=F('taxonomy_id')).values(
                'taxon_id', 'name').annotate(
                total=Count('taxonomy')
            ).order_by('name')
        )

        sites = (
            self.collection_records.annotate(
                name=F('site__site_code'),
                site_id=F('site__id')).values(
                'site_id', 'name').annotate(
                total=Count('site')
            ).order_by('name')
        )

        return {
            'total_records': self.collection_records.count(),
            'total_sites': sites.count(),
            'records': list(collections),
            'sites': list(sites)
        }
