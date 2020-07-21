# -*- coding: utf-8 -*-
"""Settings for when running under docker in development mode."""
from .dev import *  # noqa

ALLOWED_HOSTS = ['*']
USE_X_FORWARDED_HOST = True

ADMINS = (
    ('Dimas', 'dimas@kartoza.com'),
)

# Set debug to True for development
DEBUG = True
TEMPLATE_DEBUG = DEBUG
LOGGING_OUTPUT_ENABLED = DEBUG
LOGGING_LOG_SQL = DEBUG
MEDIA_ROOT = '/home/web/media'

DATABASES = {
    'default': {
        'ENGINE': 'django.contrib.gis.db.backends.postgis',
        'NAME': 'gis',
        'USER': 'docker',
        'PASSWORD': 'docker',
        'HOST': 'db',
        'PORT': 5432,
        'TEST': {
            'NAME': 'gis_test'
        },
    }
}

if os.getenv('DEFAULT_BACKEND_DATASTORE'):
    DATABASES[os.getenv('DEFAULT_BACKEND_DATASTORE')] = {
        'ENGINE': 'django.contrib.gis.db.backends.postgis',
        'NAME': 'geonode_data',
        'USER': 'geonode_data',
        'PASSWORD': 'docker',
        'HOST': 'db',
        'PORT': 5432
    }

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.memcached.MemcachedCache',
        'LOCATION': 'cache:11211',
    }
}
