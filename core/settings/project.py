# coding=utf-8

"""Project level settings.

Adjust these values as needed but don't commit passwords etc. to any public
repository!
"""

import os  # noqa
from django.utils.translation import gettext_lazy as _
from .contrib import *  # noqa

# Set languages which want to be translated
LANGUAGES = (
    ('en', _('English')),
)

VALID_DOMAIN = [
    '0.0.0.0',
]

PIPELINE = {
    'STYLESHEETS': {
        'healthyriver-base': {
            'source_filenames': {
                'js/libs/bootstrap-4.0.0/css/bootstrap.min.css',
                'js/libs/font-awesome/css/font-awesome.min.css',
                'js/libs/magnific-popup/magnific-popup.css',
                'js/libs/openlayers-4.6.4/ol.css',
                'js/libs/jquery-ui-1.12.1/jquery-ui.min.css',
                'css/base.css',
            },
            'output_filename': 'css/healthyriver-base.css',
            'extra_content': {
                'media': 'screen, projection',
            }
        }
    },
    'JAVASCRIPT': {

    }
}

REQUIRE_JS_PATH = '/static/js/libs/requirejs-2.3.5/require.js'

GRUNT_MODULES = {
    'map_view': {
        'main': 'js/app',
        'optimized': 'js/optimized.js',
    }
}

TEMP_FOLDER = MEDIA_ROOT + '/temp'

# Saving geometry of country in focused countries
FOCUSED_COUNTRIES = ["South Africa"]

# Geometry used for others
# Turn off if it is not used (like showing on map)
# If it is not used, geometry that saved is just municipals
# Because of calculating cluster is just for municipals
USE_GEOMETRY_BOUNDARY = False

# TODO(IS) Update unit test to be independent with this setting.
# Farm ID GeoServer Layer
FARM_GEOSERVER_URL = 'http://maps.kartoza.com/geoserver/kartoza/ows'
FARM_WORKSPACE = 'kartoza'
FARM_LAYER_NAME = 'farm_portion'
FARM_ID_COLUMN = 'id'

PROXY_ALLOWED_HOSTS = (
    '.kartoza.com',
    '.openstreetmap.org.za',
    '.uni-heidelberg.de',
    '.openstreetmap.org',
    '.tilehosting.com',
    '.maptiler.com',
    '.openrouteservice.org',
    '.award.org.za',
    '.fastly.net'
)

PROXY_ALLOWED_HOSTS_ENV = os.environ.get('PROXY_ALLOWED_HOSTS', None)

if PROXY_ALLOWED_HOSTS_ENV:
    proxy_list = PROXY_ALLOWED_HOSTS_ENV.split(',')
    for proxy in proxy_list:
        PROXY_ALLOWED_HOSTS += (proxy,)


PROCESSED_CSV_PATH = 'processed_csv'
SESSION_COOKIE_DOMAIN = os.environ.get('SESSION_COOKIE_DOMAIN', None)

WEBPACK_LOADER = {
    'DEFAULT': {
        'BUNDLE_DIR_NAME': 'bims/bundles/',
        'STATS_FILE': absolute_path('bims', 'webpack-stats.json'),
    }
}

CITES_TOKEN_API = os.environ.get('CITES_TOKEN_API', '')
