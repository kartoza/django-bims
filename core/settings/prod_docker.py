
"""Configuration for production server"""
# noinspection PyUnresolvedReferences
from .prod import *  # noqa
import os
import ast

from .utils import extract_replicas

DEBUG = False

ALLOWED_HOSTS = ['*']

ADMINS = (
    ('Dimas Ciputra', 'dimas@kartoza.com'),
)

DATABASES = {
    'default': {
        'ENGINE': 'bims.database_backend',
        'NAME': os.environ.get('DATABASE_NAME'),
        'USER': os.environ.get('DATABASE_USERNAME'),
        'PASSWORD': os.environ.get('DATABASE_PASSWORD'),
        'HOST': os.environ.get('DATABASE_HOST'),
        'PORT': int(os.environ.get('DATABASE_PORT', 5432)),
        'TEST_NAME': 'unittests',
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

# See fig.yml file for postfix container definition
#
EMAIL_BACKEND = 'bims.resend_email_backend.ResendBackend'
# Host for sending e-mail.
EMAIL_HOST = os.environ.get('EMAIL_HOST', 'smtp')
# Port for sending e-mail.
EMAIL_PORT = os.environ.get('EMAIL_PORT', 25)
# SMTP authentication information for EMAIL_HOST.
# See fig.yml for where these are defined
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', 'noreply@kartoza.com')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', 'docker')
EMAIL_USE_TLS = ast.literal_eval(os.environ.get('EMAIL_USE_TLS', 'False'))
EMAIL_SUBJECT_PREFIX = os.environ.get('EMAIL_SUBJECT_PREFIX', '[BIMS]')
