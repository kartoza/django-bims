import time

from celery.result import AsyncResult
from django.contrib.gis.geos import Point
from django.db.models import signals
from django.http import Http404
from rest_framework.views import APIView
from rest_framework.response import Response

from bims.models.location_site import LocationSite, location_site_post_save_handler
from bims.models.location_context_filter_group_order import (
    LocationContextFilterGroupOrder
)
from bims.models.location_type import LocationType
from bims.utils.feature_info import get_feature_centroid, get_feature_info_from_wms
from bims.enums.ecosystem_type import ECOSYSTEM_WETLAND
from bims.serializers.location_site_serializer import LocationSiteSerializer
from bims.utils.location_site import overview_site_detail


class WetlandDataApiView(APIView):
    """
    API View to handle wetland data retrieval and location site creation based on wetland layer information.
    """
    wetland_layer_name = 'kartoza:nwm6_beta_v3_20230714'

    def create_location_site(self, original_lon, original_lat, centroid):
        """
        Create or retrieve a LocationSite instance based on the centroid of a wetland layer.

        Disconnects the post_save signal before creation to avoid triggering side effects
        and reconnects it afterward if a new site is created.

        :param original_lon: Longitude of the original request point.
        :param original_lat: Latitude of the original request point.
        :param centroid: Centroid coordinates (longitude, latitude) derived from the wetland layer.

        :returns: An instance of LocationSite.
        """
        # Temporarily disconnect the post_save signal to avoid side effects during creation
        signals.post_save.disconnect(location_site_post_save_handler, sender=LocationSite)

        location_type, _ = LocationType.objects.get_or_create(
            name='PointObservation',
            allowed_geometry='POINT'
        )

        site_point = Point(centroid[1], centroid[0], srid=4326)
        location_site, created = LocationSite.objects.get_or_create(
            location_type=location_type,
            latitude=centroid[0],
            longitude=centroid[1],
            geometry_point=site_point,
            ecosystem_type=ECOSYSTEM_WETLAND,
            map_reference='Wetland layer',
        )

        if created or not location_site.wetland_id:
            # Reconnect the signal if a new location site is created or lacks a wetland ID
            signals.post_save.connect(location_site_post_save_handler, sender=LocationSite)

            # Fetch and apply wetland data from WMS
            wms_url = 'https://maps.kartoza.com/geoserver/wms'
            wms_data = get_feature_info_from_wms(
                wms_url,
                self.wetland_layer_name,
                'EPSG:4326',
                original_lon,
                original_lat,
                300,
                300
            )

            wetland_data = (
                wms_data.get(
                    'features'
                )[0].get(
                    'properties'
                ) if 'features' in wms_data and wms_data['features'] else None
            )
            if wetland_data:
                location_site.name = wetland_data.get('wetlid')
                location_site.wetland_id = wetland_data.get('wetlid')
                location_site.wetland_name = wetland_data.get('name')
                location_site.hydrogeomorphic_type = wetland_data.get('hgm_type')
                location_site.additional_data = wetland_data
                location_site.save()

        return location_site

    def get(self, request, *args, **kwargs):
        start_time = time.time()
        lat = kwargs.get('lat', '')
        lon = kwargs.get('lon', '')
        if not lat or not lon:
            raise Http404()
        lat = float(lat)
        lon = float(lon)

        wfs_url = 'https://maps.kartoza.com/geoserver/wfs'

        centroid = get_feature_centroid(
            wfs_url=wfs_url,
            layer_name=self.wetland_layer_name,
            lat=lat,
            lon=lon,
        )
        if not centroid:
            return Response({
                'message': 'layer not found'
            })

        location_site = self.create_location_site(
            original_lat=lat,
            original_lon=lon,
            centroid=centroid
        )
        task_status = {
            'state': 'STARTING'
        }

        if location_site.site_description:
            task = AsyncResult(location_site.site_description)
            task_status['state'] = task.state

        return Response({
            'data': LocationSiteSerializer(
                location_site
            ).data,
            'time': time.time() - start_time,
            'task_status': task_status,
            'site_details': overview_site_detail(location_site.id)
        })
