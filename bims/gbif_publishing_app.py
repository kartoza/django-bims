from django.apps import AppConfig


class GbifPublishingConfig(AppConfig):
    # Lightweight config to provide an app label for admin grouping.
    name = 'bims.gbif_publishing_app'
    label = 'gbif_publishing'
    verbose_name = 'GBIF Publishing'
