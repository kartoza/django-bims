# coding=utf-8
from rest_framework.views import APIView, Response
from django.contrib.gis.geos import GEOSGeometry, Point
from django.contrib.gis.measure import D
from django.contrib.gis.db.models.functions import Distance
from bims.models.location_site import LocationSite


class SiteByCoord(APIView):
    """ Get site by coordinates """

    def get(self, request):
        lat = request.GET.get('lat', None)
        lon = request.GET.get('lon', None)
        radius = request.GET.get('radius', 0.0)
        process_id = request.GET.get('process_id', None)
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
            location_sites = LocationSite.objects.filter(
                biological_collection_record__validated=True
            ).distinct()
        else:
            location_sites = LocationSite.objects.all()

        location_sites = location_sites.filter(
            geometry_point__distance_lte=(point, D(km=radius))
        ).annotate(
            distance=Distance('geometry_point', point)
        ).order_by('distance')

        responses = []
        for site in location_sites:
            responses.append({
                'id': site.id,
                'name': site.name,
                'latitude': site.get_centroid().y,
                'longitude': site.get_centroid().x
            })

        return Response(responses)
