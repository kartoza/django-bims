import json
from django.db import models
from django.contrib.postgres.fields import JSONField
from preferences.models import Preferences


class SiteSetting(Preferences):
    site_notice = models.TextField(
        null=True,
        blank=True
    )

    map_default_filters = JSONField(
        default=[],
        help_text='Which filters are selected by default, '
                  'the format must be as follows : '
                  '[{"filter_key": "sourceCollection", '
                  '"filter_values": ["bims"]}]'
    )

    default_location_site_cluster = models.CharField(
        max_length=100,
        help_text='SQL view name of the location site cluster which '
                  'used on the map',
        default='default_location_site_cluster'
    )

    default_data_source = models.CharField(
        max_length=100,
        help_text='Default data source when adding new collection',
        null=True,
        blank=True
    )

    default_team_name = models.CharField(
        max_length=150,
        help_text='Default team name',
        null=True,
        blank=True
    )

    def save(self, *args, **kwargs):
        max_allowed = 10
        attempt = 0
        is_dictionary = False

        while not is_dictionary and attempt < max_allowed:
            if not self.map_default_filters:
                break
            if isinstance(self.map_default_filters, list):
                is_dictionary = True
            else:
                self.map_default_filters = json.loads(self.map_default_filters)
                attempt += 1
        super(SiteSetting, self).save(*args, **kwargs)
