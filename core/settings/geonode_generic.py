# -*- coding: utf-8 -*-
#########################################################################
#
# Copyright (C) 2017 OSGeo
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#
#########################################################################

# Django settings for the GeoNode project.
import os
import urllib.parse as urlparse
from geonode.settings import *  # noqa

#
# General Django development settings
#

# we need hostname for deployed
surl = urlparse(SITEURL)
hostname = surl.hostname

# add trailing slash to site url. geoserver url will be relative to this
if not SITEURL.endswith('/'):
    SITEURL = '{}/'.format(SITEURL)

SITENAME = os.getenv("SITENAME", 'geonode_generic')

# Defines the directory that contains the settings file as the LOCAL_ROOT
# It is used for relative settings elsewhere.
LOCAL_ROOT = os.path.abspath(os.path.dirname(__file__))

try:
    ALLOWED_HOSTS = ast.literal_eval(os.getenv('ALLOWED_HOSTS'))
except:  # noqa
    ALLOWED_HOSTS = ['localhost', ] if os.getenv('ALLOWED_HOSTS') is None \
        else re.split(r' *[,|:|;] *', os.getenv('ALLOWED_HOSTS'))

_PROXY_OSM = ('nominatim.openstreetmap.org',)
try:
    PROXY_ALLOWED_HOSTS += _PROXY_OSM
except NameError:
    PROXY_ALLOWED_HOSTS = _PROXY_OSM

# AUTH_IP_WHITELIST property limits access to users/groups REST endpoints
# to only whitelisted IP addresses.
#
# Empty list means 'allow all'
#
# If you need to limit 'api' REST calls to only some specific IPs
# fill the list like below:
#
# AUTH_IP_WHITELIST = ['192.168.1.158', '192.168.1.159']
AUTH_IP_WHITELIST = []

MANAGERS = ADMINS = os.getenv('ADMINS', [])

# Location of locale files
LOCALE_PATHS = (
    os.path.join(LOCAL_ROOT, 'locale'),
) + LOCALE_PATHS

loaders = (
        TEMPLATES[0]['OPTIONS'].get('loaders') or
        [
            'django.template.loaders.filesystem.Loader',
            'django.template.loaders.app_directories.Loader'
        ]
)
# loaders.insert(0, 'apptemplates.Loader')
TEMPLATES[0]['OPTIONS']['loaders'] = loaders
TEMPLATES[0].pop('APP_DIRS', None)

MONITORING_HOST_NAME = os.getenv("MONITORING_HOST_NAME", hostname)
MONITORING_SERVICE_NAME = 'geonode'
