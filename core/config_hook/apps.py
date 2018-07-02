# coding=utf-8
from geonode.base import BaseAppConfig


class AppConfig(BaseAppConfig):

    name = "core"
    label = "core"

    def ready(self):
        super(AppConfig, self).ready()
        # check settings
        from django.conf import settings

        installed_apps = []
        for app in settings.INSTALLED_APPS:
            if isinstance(app, basestring):
                installed_apps.append(app)

        settings.INSTALLED_APPS = installed_apps
