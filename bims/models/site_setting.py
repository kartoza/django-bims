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

    spatial_filter_layer_style = models.CharField(
        max_length=100,
        help_text='Style name for spatial filter layer',
        default='red_outline',
        blank=True
    )

    github_feedback_repo = models.CharField(
        max_length=100,
        help_text='Github repo for users`s feedback',
        default='',
        blank=True
    )

    github_feedback_token = models.CharField(
        max_length=100,
        help_text='Access token for Github feedback repo',
        default='',
        blank=True
    )

    geocontext_keys = models.CharField(
        max_length=300,
        help_text='Default location context group keys that will be fetched '
                  'from Geocontext, separated by commas.',
        default='political_boundary_group,rainfall_group',
        blank=True
    )

    disclaimer_form_text = models.CharField(
        max_length=300,
        default='I agree to these data being shared via the FBIS '
                'platform for visualisation and download by '
                'registered FBIS users',
        blank=True
    )

    disclaimer_doc_text = models.CharField(
        max_length=300,
        default='I hereby confirm that I am the owner of these '
                'data and/or document and agree to these being shared '
                'via the FBIS platform for download by registered FBIS users.',
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
