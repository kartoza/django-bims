# SPDX-FileCopyrightText: Kartoza
# SPDX-License-Identifier: AGPL-3.0
#
# Local development settings for Django BIMS (Nix environment)
# Use this with: DJANGO_SETTINGS_MODULE=core.settings.dev_local
#
# Made with love by Kartoza | https://kartoza.com

import os
from .dev import *  # noqa

# Debug settings
DEBUG = True
TEMPLATE_DEBUG = DEBUG

# Get project root (where manage.py is)
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Local PostgreSQL via Nix (socket connection)
# Uses bims.database_backend which wraps django_tenants for multi-tenant support
DATABASES = {
    'default': {
        'ENGINE': 'bims.database_backend',
        'NAME': os.environ.get('DATABASE_NAME', 'bims'),
        'USER': os.environ.get('DATABASE_USERNAME', os.environ.get('USER', 'postgres')),
        'PASSWORD': os.environ.get('DATABASE_PASSWORD', ''),
        'HOST': os.environ.get('DATABASE_HOST', os.path.join(PROJECT_ROOT, '.pgdata')),
        'PORT': os.environ.get('DATABASE_PORT', '5432'),
        'TEST': {
            'NAME': 'test_bims',
        },
    }
}

# Original backend for django-tenants PostGIS support
ORIGINAL_BACKEND = "django.contrib.gis.db.backends.postgis"

# No replicas in local development
REPLICA_ENV_VAR = ""

# Allowed hosts for local development
ALLOWED_HOSTS = ['*', 'localhost', '127.0.0.1', '0.0.0.0']

# Static and media files for local development
STATIC_ROOT = os.path.join(PROJECT_ROOT, 'static')
MEDIA_ROOT = os.path.join(PROJECT_ROOT, 'media')

# Disable SSL redirect for local development
SECURE_SSL_REDIRECT = False
CSRF_COOKIE_SECURE = False
SESSION_COOKIE_SECURE = False

# Console email backend for development
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Disable caching for development
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
    }
}

# Celery settings for local development
CELERY_BROKER_URL = os.environ.get('CELERY_BROKER_URL', 'amqp://guest:guest@localhost:5672/')
CELERY_RESULT_BACKEND = 'django-db'
CELERY_TASK_ALWAYS_EAGER = os.environ.get('CELERY_TASK_ALWAYS_EAGER', 'False').lower() == 'true'

# Local GeoServer (if running)
GEOSERVER_LOCATION = os.environ.get('GEOSERVER_LOCATION', 'http://localhost:8080/geoserver/')
GEOSERVER_PUBLIC_LOCATION = os.environ.get('GEOSERVER_PUBLIC_LOCATION', 'http://localhost:8080/geoserver/')

# Site URL
SITEURL = os.environ.get('SITEURL', 'http://localhost:8000/')

# Logging configuration for development
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': os.environ.get('DJANGO_LOG_LEVEL', 'INFO'),
            'propagate': False,
        },
        'bims': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
}

# Debug toolbar settings
INTERNAL_IPS = ['127.0.0.1', 'localhost']

# Disable GeoContext for local development (unless configured)
GEOCONTEXT_URL = os.environ.get('GEOCONTEXT_URL', '')

# Webpack loader for development
WEBPACK_LOADER = {
    'DEFAULT': {
        'BUNDLE_DIR_NAME': 'bims/bundles/',
        'STATS_FILE': os.path.join(PROJECT_ROOT, 'bims', 'webpack-stats.json'),
        'POLL_INTERVAL': 0.1,
        'IGNORE': [r'.+\.hot-update.js', r'.+\.map'],
    },
    # V2: New React + TypeScript + Chakra UI frontend
    'V2': {
        'BUNDLE_DIR_NAME': 'bims/bundles/v2/',
        'STATS_FILE': os.path.join(PROJECT_ROOT, 'bims', 'webpack-stats-v2.json'),
    }
}

# CSRF trusted origins for local development
CSRF_TRUSTED_ORIGINS = [
    'http://localhost:8000',
    'http://localhost:8080',
    'http://127.0.0.1:8000',
    'http://127.0.0.1:8080',
]

# Pipeline settings for development
PIPELINE = {
    'PIPELINE_ENABLED': False,
    'STYLESHEETS': {},
    'JAVASCRIPT': {},
}
