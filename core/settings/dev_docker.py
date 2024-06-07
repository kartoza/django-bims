# -*- coding: utf-8 -*-
"""Settings for when running under docker in development mode."""
from .dev import *  # noqa

from .utils import extract_replicas

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
STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'

DATABASES = {
    'default': {
        'ENGINE': 'django_tenants.postgresql_backend',
        'NAME': 'app',
        'USER': 'docker',
        'PASSWORD': 'docker',
        'HOST': 'db',
        'PORT': 5432,
        'TEST': {
            'NAME': 'gis_test'
        },
        'DATABASE': 'default'
    }
}

ORIGINAL_BACKEND = "django.contrib.gis.db.backends.postgis"

REPLICA_ENV_VAR = os.getenv("DB_REPLICAS", "")
REPLICAS = extract_replicas(REPLICA_ENV_VAR)
for index, replica in enumerate(REPLICAS, start=1):
    DATABASES[f'replica_{index}'] = {
        'ENGINE': os.getenv('DB_ENGINE', 'django_tenants.postgresql_backend'),
        'NAME': replica['NAME'],
        'USER': replica['USER'],
        'PASSWORD': replica['PASSWORD'],
        'HOST': replica['HOST'],
        'PORT': replica['PORT'],
        'DATABASE': f'replica_{index}'
    }

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.memcached.PyMemcacheCache',
        'LOCATION': 'cache:11211',
        'KEY_FUNCTION': 'django_tenants.cache.make_key',
        'REVERSE_KEY_FUNCTION': 'django_tenants.cache.reverse_key',
    }
}
