# SPDX-FileCopyrightText: Kartoza
# SPDX-License-Identifier: AGPL-3.0
"""
Development settings for Nix-based development environment.

This settings file is designed for use with the Nix flake development
environment, using a local PostgreSQL instance with PostGIS.
"""

import os
from pathlib import Path

from .project import *  # noqa: F401, F403

# Debug settings
DEBUG = True
TEMPLATE_DEBUG = DEBUG
LOGGING_OUTPUT_ENABLED = DEBUG
LOGGING_LOG_SQL = DEBUG

# Email backend for development
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# Disable caching in development
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.dummy.DummyCache",
    }
}

# Static files storage
STATICFILES_STORAGE = "django.contrib.staticfiles.storage.StaticFilesStorage"

# Pipeline settings
PIPELINE["PIPELINE_ENABLED"] = False  # noqa: F405

# Allow all hosts in development
ALLOWED_HOSTS = ["*"]
PROXY_ALLOWED_HOSTS = ("*",)

# Database configuration for Nix environment
# Uses Unix socket connection to local PostgreSQL
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

DATABASES = {
    "default": {
        "ENGINE": "bims.database_backend",
        "NAME": os.environ.get("DATABASE_NAME", "bims"),
        "USER": os.environ.get("DATABASE_USERNAME", os.environ.get("USER", "postgres")),
        "PASSWORD": os.environ.get("DATABASE_PASSWORD", ""),
        # Use Unix socket if DATABASE_HOST points to a directory
        "HOST": os.environ.get("DATABASE_HOST", str(PROJECT_ROOT / ".pgdata")),
        "PORT": os.environ.get("DATABASE_PORT", "5432"),
        "TEST": {
            "NAME": "test_bims",
        },
    }
}

# Original backend for django-tenants PostGIS support
ORIGINAL_BACKEND = "django.contrib.gis.db.backends.postgis"

# No replicas in development
REPLICA_ENV_VAR = ""

# Static and media paths for development
STATIC_ROOT = str(PROJECT_ROOT / "static")
MEDIA_ROOT = str(PROJECT_ROOT / "media")

# Celery settings for development
CELERY_BROKER_URL = os.environ.get("CELERY_BROKER_URL", "amqp://guest:guest@localhost:5672//")
CELERY_RESULT_BACKEND = "django-db"
CELERY_TASK_ALWAYS_EAGER = os.environ.get("CELERY_TASK_ALWAYS_EAGER", "False").lower() == "true"

# Debug toolbar
if DEBUG:
    try:
        import debug_toolbar  # noqa: F401

        INSTALLED_APPS += ["debug_toolbar"]  # noqa: F405
        MIDDLEWARE = ["debug_toolbar.middleware.DebugToolbarMiddleware"] + list(MIDDLEWARE)  # noqa: F405
        INTERNAL_IPS = ["127.0.0.1", "localhost"]
    except ImportError:
        pass

# Logging configuration for development
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {module} {process:d} {thread:d} {message}",
            "style": "{",
        },
        "simple": {
            "format": "{levelname} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "simple",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": os.environ.get("DJANGO_LOG_LEVEL", "INFO"),
            "propagate": False,
        },
        "bims": {
            "handlers": ["console"],
            "level": "DEBUG",
            "propagate": False,
        },
    },
}

# CORS settings for development
CORS_ALLOW_ALL_ORIGINS = True

# CSRF settings for development
CSRF_TRUSTED_ORIGINS = [
    "http://localhost:8000",
    "http://localhost:8080",
    "http://127.0.0.1:8000",
    "http://127.0.0.1:8080",
]

# Site URL for development
SITEURL = os.environ.get("SITEURL", "http://localhost:8000/")

# GeoContext URL
GEOCONTEXT_URL = os.environ.get("GEOCONTEXT_URL", "https://geocontext.kartoza.com")

# Disable Sentry in development
SENTRY_DSN = None
