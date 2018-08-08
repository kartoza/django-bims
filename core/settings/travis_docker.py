# -*- coding: utf-8 -*-
from .prod_docker import *  # noqa

DJANGO_EASY_AUDIT_WATCH_MODEL_EVENTS = False
DJANGO_EASY_AUDIT_UNREGISTERED_CLASSES_EXTRA = [
    'layers.Layer',
]
