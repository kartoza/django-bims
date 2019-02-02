import json
import hashlib
from django.db.models import Q, Count, F
from django.contrib.gis.db.models import Union
from rest_framework.views import APIView
from rest_framework.response import Response
from bims.models import (
    BiologicalCollectionRecord,
    Boundary,
    UserBoundary,
    SearchProcess,
    SEARCH_RESULTS,
    SEARCH_PROCESSING
)
from bims.tasks.search_version_2 import search_task

MAX_PAGINATED_SITES = 20


class SearchVersion2APIView(APIView):
    """
    Search with django query
    """

    def get(self, request):
        parameters = request.GET
        search_uri = request.build_absolute_uri()
        search_process, created = SearchProcess.objects.get_or_create(
            category=SEARCH_RESULTS,
            query=search_uri
        )

        results = search_process.get_file_if_exits()
        if results:
            results['process_id'] = search_process.process_id
            if 'sites' in results:
                results['total_unique_sites'] = len(results['sites'])
                results['sites'] = results['sites'][:MAX_PAGINATED_SITES]
            results['total_unique_taxa'] = len(results['records'])
            raw = search_process.search_raw_query
            results['sites_raw_query'] = raw[
                raw.find('WHERE') + 6:
                len(raw)
            ]
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

        # call worker task
        search_task.delay(
            parameters,
            search_process.id,
        )

        result_file = search_process.get_file_if_exits(finished=False)
        if result_file:
            return Response(result_file)
        return Response({'status': 'result/status not exists'})


class SearchVersion2(object):

    location_sites_raw_query = ''
    collection_records = None

    def __init__(self, parameters):
        self.parameters = parameters
        super(SearchVersion2, self).__init__()

    def get_request_data(self, field, default_value=None):
        return self.parameters.get(field, default_value)

    def parse_request_json(self, field):
        json_query = self.get_request_data(field=field)
        if json_query:
            return json.loads(json_query)
        else:
            return None

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

    def process_search(self):
        if self.search_query:
            bio = BiologicalCollectionRecord.objects.filter(
                Q(original_species_name__icontains=self.search_query) |
                Q(taxonomy__scientific_name__icontains=self.search_query)
            )
        else:
            bio = BiologicalCollectionRecord.objects.all()

        filters = dict()
        filters['validated'] = True
        filters['taxonomy__isnull'] = False
        if self.site_ids:
            filters['site__in'] = self.site_ids
        if self.categories:
            filters['category__in'] = self.categories
        if self.reference_category:
            filters['reference_category__in'] = self.reference_category
        if self.year_ranges:
            filters['collection_date__range'] = self.year_ranges
        if self.months:
            filters['collection_date__month__in'] = self.months
        if self.collector:
            filters['collector__in'] = self.collector
        if self.reference:
            filters['reference__in'] = self.reference
        if self.conservation_status:
            filters['taxonomy__iucn_status__category__in'] = (
                self.conservation_status
            )
        if self.endemic:
            filters['taxonomy__endemism__name__in'] = (
                self.endemic
            )
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
                print(len(boundary))
                geometry_found = boundary[0].geometry
            if geometry_found:
                filters['site__boundary__in'] = boundary
        bio = bio.filter(**filters)

        if self.user_boundary:
            user_boundaries = UserBoundary.objects.filter(
                pk__in=self.user_boundary
            )
            if user_boundaries:
                bio.filter(site__geometry_point__intersent=(
                    user_boundaries.aggregate(area=Union('geometry'))['area']
                ))
        self.location_sites_raw_query = bio.distinct('site').values(
            'site_id',
            'site__geometry_point',
            'site__name').query

        self.collection_records = bio
        return self.collection_records

    def get_summary_data(self):
        if not self.collection_records:
            self.process_search()

        collections = (
            self.collection_records.annotate(
                name=F('taxonomy__scientific_name'),
                taxon_id=F('taxonomy_id')).values(
                'taxon_id', 'name').annotate(total=Count('taxonomy'))
        )

        sites = (
            self.collection_records.annotate(
                name=F('site__name'),
                site_id=F('site__id')).values(
                'site_id', 'name').annotate(total=Count('site')))

        return {
            'total_records': len(self.collection_records),
            'total_sites': len(sites),
            'records': list(collections),
            'sites': list(sites)
        }
