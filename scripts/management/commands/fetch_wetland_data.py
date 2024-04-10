from django.core.management.base import BaseCommand
from bims.utils.feature_info import get_feature_centroid


class Command(BaseCommand):
    help = 'Fetch wetland data'

    def add_arguments(self, parser):
        parser.add_argument(
            '-lat',
            '--lat',
            dest='lat',
            default='30.0',
        )
        parser.add_argument(
            '-lon',
            '--lon',
            dest='lon',
            default='30.0',
        )

    def handle(self, *args, **options):
        lat = float(options.get('lat', '30.0'))
        lon = float(options.get('lon', '30.0'))
        wetland_layer_name = 'kartoza:nwm6_beta_v3_20230714'
        wfs_url = 'https://maps.kartoza.com/geoserver/wfs'
        centroid = get_feature_centroid(
            lon,
            lat,
            wfs_url=wfs_url,
            layer_name=wetland_layer_name
        )
        print(centroid)
