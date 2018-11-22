# -*- coding: utf-8 -*-
"""Settings for when running under docker in development mode."""
from .dev import *  # noqa

ALLOWED_HOSTS = ['*',
                 u'0.0.0.0']

ADMINS = (
    ('Anita Hapsari', 'anita@kartoza.com'),
)

# Set debug to True for development
DEBUG = True
TEMPLATE_DEBUG = DEBUG
LOGGING_OUTPUT_ENABLED = DEBUG
LOGGING_LOG_SQL = DEBUG

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

HAYSTACK_CONNECTIONS = {
    'default': {
        'ENGINE': 'bims.search_backends.fuzzy_elastic_search_engine'
                  '.FuzzyElasticSearchEngine',
        'URL': 'http://elasticsearch:9200/',
        'INDEX_NAME': 'haystack',
    },
}

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.memcached.MemcachedCache',
        'LOCATION': 'cache:11211',
    }
}
