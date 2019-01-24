import json
from django.db.models import Q, Count, F
from rest_framework.views import APIView
from rest_framework.response import Response
from bims.models import (
    BiologicalCollectionRecord,
    Boundary
)


class SearchVersion2(APIView):

    def get_request_data(self, field, default_value=None):
        return self.request.GET.get(field, default_value)

    def get_json_data(self, field):
        json_query = self.get_request_data(field=field)
        if json_query:
            return json.loads(json_query)
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
        return self.get_json_data('referenceCategory')

    @property
    def categories(self):
        return self.get_json_data('category')

    @property
    def collector(self):
        return self.get_json_data('collector')

    @property
    def reference(self):
        return self.get_json_data('reference')

    @property
    def conservation_status(self):
        return self.get_json_data('conservationStatus')

    @property
    def boundary(self):
        return self.get_json_data('boundary')

    def get(self, request):
        if self.search_query:
            bio = BiologicalCollectionRecord.objects.filter(
                Q(original_species_name__icontains=self.search_query) |
                Q(taxonomy__scientific_name__icontains=self.search_query)
            )
        else:
            bio = BiologicalCollectionRecord.objects.all()

        filters = {}
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

        total_records = len(bio)
        collections = bio.annotate(name=F('taxonomy__scientific_name'),
                                   taxon_id=F('taxonomy_id')).values(
            'taxon_id', 'name').annotate(total=Count('taxonomy'))
        return Response({
            'total_records': total_records,
            'records': collections
        })
