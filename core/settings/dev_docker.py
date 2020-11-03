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
        'USER': 'docker',
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

# See fig.yml file for postfix container definition
#
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
# Host for sending e-mail.
EMAIL_HOST = 'smtp.gmail.com'
# Port for sending e-mail.
EMAIL_PORT = 587
# SMTP authentication information for EMAIL_HOST.
# See fig.yml for where these are defined
EMAIL_HOST_USER = 'bob.joko.test@gmail.com'
EMAIL_HOST_PASSWORD = '~XG&K`aQvH9/y_8z'
EMAIL_USE_TLS = True
EMAIL_SUBJECT_PREFIX = os.environ.get('EMAIL_SUBJECT_PREFIX', '[BIMS]')
