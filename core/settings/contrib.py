# coding=utf-8
"""
core.settings.contrib
"""
from core.settings.utils import ensure_unique_app_labels
from .base import *  # noqa
# Override base settings from geonode
from geonode_generic.settings import *  # noqa
from .celery_settings import *  # noqa
import os
try:
    from .secret import IUCN_API_KEY  # noqa
except ImportError:
    IUCN_API_KEY = ''


STOP_WORDS = (
    'a', 'an', 'and', 'if', 'is', 'the', 'in', 'i', 'you', 'other',
    'this', 'that', 'to',
)

STATICFILES_STORAGE = 'pipeline.storage.PipelineCachedStorage'
STATICFILES_FINDERS += (
    'pipeline.finders.PipelineFinder',
)

# Django-allauth related settings
AUTHENTICATION_BACKENDS = (
    # Needed to login by username in Django admin, regardless of `allauth`
    'django.contrib.auth.backends.ModelBackend',

    # `allauth` specific authentication methods, such as login by e-mail
    'allauth.account.auth_backends.AuthenticationBackend',
)

# Django grappelli need to be added before django.contrib.admin
INSTALLED_APPS = (
    'grappelli',
) + INSTALLED_APPS

# Grapelli settings
GRAPPELLI_ADMIN_TITLE = 'Bims Admin Page'

INSTALLED_APPS += (
    # AppConfig Hook to fix issue from geonode
    'core.config_hook',
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google',
    'allauth.socialaccount.providers.github',
    'easyaudit',
    'rolepermissions',
    'rest_framework',
    'celery',
    'pipeline',
    'modelsdoc',
    'contactus',
    'haystack',
    'django_prometheus',
    'ckeditor',
)

# workaround to get flatpages picked up in installed apps.
INSTALLED_APPS += (
    'django.contrib.flatpages',
)

# Set templates
try:
    TEMPLATES[0]['DIRS'] = [
        absolute_path('core', 'base_templates'),
        absolute_path('bims', 'templates'),
        absolute_path('example', 'templates'),
    ] + TEMPLATES[0]['DIRS']

    TEMPLATES[0]['OPTIONS']['context_processors'] += [
        'bims.context_processor.add_recaptcha_key',
        'bims.context_processor.custom_navbar_url'
    ]
except KeyError:
    TEMPLATES = [
        {
            'BACKEND': 'django.template.backends.django.DjangoTemplates',
            'DIRS': [
                # project level templates
                absolute_path('core', 'base_templates'),
                absolute_path('bims', 'templates'),
                absolute_path('example', 'templates'),
            ],
            'APP_DIRS': True,
            'OPTIONS': {
                'context_processors': [
                    'django.template.context_processors.debug',
                    'django.template.context_processors.request',
                    'django.contrib.auth.context_processors.auth',
                    'django.contrib.messages.context_processors.messages',

                    # `allauth` needs this from django
                    'django.template.context_processors.request',
                    'bims.context_processor.add_recaptcha_key',
                    'bims.context_processor.custom_navbar_url'
                ],
            },
        },
    ]

# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' "static/" subdirectories and in STATICFILES_DIRS.
# Example: "/var/www/example.com/static/"
STATIC_ROOT = '/home/web/static'

# Additional locations of static files
STATICFILES_DIRS = [
    # Put strings here, like "/home/html/static" or "C:/www/django/static".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    absolute_path('core', 'base_static'),
    absolute_path('bims', 'static'),
] + STATICFILES_DIRS

INSTALLED_APPS = ensure_unique_app_labels(INSTALLED_APPS)

MIDDLEWARE_CLASSES += (
    'easyaudit.middleware.easyaudit.EasyAuditMiddleware',
    'django_prometheus.middleware.PrometheusBeforeMiddleware',
)

# for middleware in MIDDLEWARE_CLASSES:
#     if middleware not in MIDDLEWARE:
#         MIDDLEWARE += (middleware,)

# Defines whether to log model related events,
# such as when an object is created, updated, or deleted
DJANGO_EASY_AUDIT_WATCH_MODEL_EVENTS = True

# Defines whether to log user authentication events,
# such as logins, logouts and failed logins.
DJANGO_EASY_AUDIT_WATCH_AUTH_EVENTS = True

# Defines whether to log URL requests made to the project
DJANGO_EASY_AUDIT_WATCH_REQUEST_EVENTS = False

SOCIALACCOUNT_PROVIDERS = {
    'github': {
        'SCOPE': ['user:email', 'public_repo', 'read:org']
    }
}

ACCOUNT_UNIQUE_EMAIL = True
ACCOUNT_USERNAME_REQUIRED = True
ACCOUNT_EMAIL_REQUIRED = True
# ACCOUNT_SIGNUP_FORM_CLASS = 'base.forms.SignupForm'
ACCOUNT_AUTHENTICATION_METHOD = 'username_email'
LOGIN_REDIRECT_URL = "/"

# ROLEPERMISSIONS_MODULE = 'roles.settings.roles'

IUCN_API_URL = 'http://apiv3.iucnredlist.org/api/v3'

CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'

BROKER_URL = 'amqp://guest:guest@%s:5672//' % os.environ['RABBITMQ_HOST']

# django modelsdoc settings
MODELSDOC_APPS = ('bims', 'fish', 'reptile',)

MODELSDOC_OUTPUT_FORMAT = 'rst'
MODELSDOC_MODEL_WRAPPER = 'modelsdoc.wrappers.ModelWrapper'
MODELSDOC_FIELD_WRAPPER = 'modelsdoc.wrappers.FieldWrapper'
MODELSDOC_INCLUDE_AUTO_CREATED = True

# contact us email
CONTACT_US_EMAIL = os.environ['CONTACT_US_EMAIL']

ELASTIC_MIN_SCORE = 2

DJANGO_EASY_AUDIT_UNREGISTERED_CLASSES_EXTRA = [
    'layers.Layer',
    'monitoring.RequestEvent',
    'monitoring.MonitoredResource',
]

ACCOUNT_AUTHENTICATED_LOGIN_REDIRECTS = False
