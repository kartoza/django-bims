# coding=utf-8
from django.apps import AppConfig


class AppConfig(AppConfig):

    name = "core"
    label = "core"

    def ready(self):
        super(AppConfig, self).ready()
        from django.conf import settings
        from django.db.models.signals import post_migrate

        def create_taxonomy_indexes(sender, **kwargs):
            from bims.utils.add_index import add_indexes_for_taxonomy
            add_indexes_for_taxonomy()

        post_migrate.connect(create_taxonomy_indexes, sender=self)

        installed_apps = []

        for app in settings.INSTALLED_APPS:
            if isinstance(app, str):
                installed_apps.append(app)

        settings.INSTALLED_APPS = installed_apps
