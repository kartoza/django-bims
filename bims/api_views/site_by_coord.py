# coding=utf-8
from rest_framework.views import APIView, Response
from django.contrib.gis.geos import Point
from django.contrib.gis.measure import D
from django.contrib.gis.db.models.functions import Distance
from bims.models.location_site import LocationSite
from bims.api_views.search import Search


class SiteByCoord(APIView):
    """ List closest sites by coordinates """

    def get(self, request):
        """
        Get closest sites by lat, long, and radius provided in request
        parameter
        :param request: get request object
        :return: list of dict of site data e.g. {
            'id': 1,
            'name': 'site',
            'site_code': '121',
            'distance_m': 1,
            'latitude': -12,
            'longitude': 23
        }
        """
        lat = request.GET.get('lat', None)
        lon = request.GET.get('lon', None)
        radius = request.GET.get('radius', 0.0)
        process_id = request.GET.get('process_id', None)
        search_mode = request.GET.get('search_mode', None)
        radius = float(radius)

        if not lat or not lon:
            return Response('Missing lat/lon')

        try:
            lat = float(lat)
            lon = float(lon)
            point = Point(lon, lat)
        except (ValueError, TypeError):
            return Response('Invalid lat or lon format')

        if not process_id:
            site_filters = {
                'biological_collection_record__validated': True
            }
            if search_mode:
                search = Search(request.GET.dict())
                collection_results = search.process_search()
                collection_result_ids = list(collection_results.values_list(
                    'id', flat=True
                ))
                site_filters['biological_collection_record__id__in'] = (
                    collection_result_ids
                )
            location_sites = LocationSite.objects.filter(
                **site_filters
            ).distinct()
        else:
            location_sites = LocationSite.objects.all()

        location_sites = location_sites.filter(
            geometry_point__distance_lte=(point, D(km=radius))
        ).annotate(
            distance=Distance('geometry_point', point)
        ).order_by('distance')[:10]

        responses = []
        for site in location_sites:
            responses.append({
                'id': site.id,
                'name': site.name,
                'site_code': site.site_code,
                'distance_m': site.distance.m,
                'latitude': site.get_centroid().y,
                'longitude': site.get_centroid().x
            })

        return Response(responses)
