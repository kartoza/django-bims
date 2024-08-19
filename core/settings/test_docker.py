# -*- coding: utf-8 -*-
from .test import *  # noqa

ALLOWED_HOSTS = ['*',
                 u'0.0.0.0']

ADMINS = (
    ('Dimas Ciputra', 'dimas@kartoza.com'),
)

# Set debug to True for development
DEBUG = True
TEMPLATE_DEBUG = DEBUG
LOGGING_OUTPUT_ENABLED = DEBUG
LOGGING_LOG_SQL = DEBUG

DATABASES = {
    'default': {
        'ENGINE': 'django_tenants.postgresql_backend',
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

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.filebased.FileBasedCache",
        "LOCATION": "/var/tmp/django_cache",
    }
}
DJANGO_EASY_AUDIT_WATCH_MODEL_EVENTS = False

ACCOUNT_EMAIL_VERIFICATION = 'none'
STATICFILES_STORAGE = 'pipeline.storage.NonPackagingPipelineStorage'
PIPELINE_ENABLED = False

CELERY_TASK_ALWAYS_EAGER = True
CELERY_BROKER_URL = 'memory://'
CELERY_RESULT_BACKEND_PATH = os.getenv(
    'CELERY_RESULT_BACKEND_PATH',
    os.path.join(PROJECT_ROOT, '.celery_results'))
if not os.path.exists(CELERY_RESULT_BACKEND_PATH):
    os.makedirs(CELERY_RESULT_BACKEND_PATH)
CELERY_RESULT_BACKEND = 'file:///%s' % CELERY_RESULT_BACKEND_PATH

DATABASE_ALIAS_FROM_DOMAIN = ast.literal_eval(
    os.getenv(
        'DATABASE_ALIAS_FROM_DOMAIN',
        '{"dev.bims.orb.local": "test2"}')
)
