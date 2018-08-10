
__author__ = 'timlinux'

# -*- coding: utf-8 -*-
from .test import *  # noqa

DATABASES = {
    'default': {
        'ENGINE': 'django.contrib.gis.db.backends.postgis',
        'NAME': 'test_db',
        'USER': 'postgres',
        'PASSWORD': '',
        'HOST': 'localhost',
        # Set to empty string for default.
        'PORT': '',
    }
}

MEDIA_ROOT = '/tmp/media'
STATIC_ROOT = '/tmp/static'

HAYSTACK_CONNECTIONS = {
    'default': {
        'ENGINE': 'bims.search_backends.fuzzy_elastic_search_engine'
                  '.FuzzyElasticSearchEngine',
        'URL': 'http://localhost:9200/',
        'INDEX_NAME': 'haystack',
    },
}
