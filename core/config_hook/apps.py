# coding=utf-8
from django.apps import AppConfig


class AppConfig(AppConfig):

    name = "core"
    label = "core"

    def ready(self):
        super(AppConfig, self).ready()
        # check settings
        from django.conf import settings

        installed_apps = []

        # Fix python 3 compatibility
        try:
            basestring
        except NameError:
            basestring = str

        for app in settings.INSTALLED_APPS:
            if isinstance(app, basestring):
                installed_apps.append(app)

        settings.INSTALLED_APPS = installed_apps
