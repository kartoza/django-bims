import json
from django.db import models
from django.contrib.postgres.fields import JSONField
from preferences.models import Preferences


class SiteSetting(Preferences):
    SITE_CODE_GENERATOR_CHOICES = (
        ('bims', 'BIMS (2 Site Name + 2 Site Description + Site count)'),
        ('fbis', 'FBIS (2 Secondary catchment + 4 River + Site count)'),
        (
            'rbis',
            'RBIS (1 Catchment 0 + 2 Catchment 1 + 1 Catchment 2 + Site count)'
        ),
    )
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

    default_site_name = models.CharField(
        max_length=150,
        help_text='Default site name',
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

    geocontext_keys = models.TextField(
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

    default_basemap = models.CharField(
        max_length=100,
        default='Terrain',
        help_text='The default basemap layer that is displayed on the map'
    )

    default_center_map = models.CharField(
        max_length=100,
        default='22.948492328125,-31.12543669218031',
    )

    default_extent_map = models.CharField(
        max_length=100,
        default='5.207535937500003,-37.72038269917067,47.3950359375,'
                '-18.54426493227018'
    )

    blog_page_link = models.CharField(
        blank=True,
        max_length=100,
        help_text='Link to blog page'
    )

    docs_page_link = models.CharField(
        blank=True,
        max_length=100,
        help_text='Link to docs page'
    )

    site_code_generator = models.CharField(
        max_length=50,
        choices=SITE_CODE_GENERATOR_CHOICES,
        blank=True,
        default='bims',
        help_text='How site code generated'
    )

    base_country_code = models.CharField(
        max_length=100,
        blank=True,
        default='',
        help_text='Base country code for the site, '
                  'using ISO 3166-1 (See here for the list : '
                  'https://wiki.openstreetmap.org/wiki/Nominatim/'
                  'Country_Codes)'
    )

    show_third_party_layer = models.BooleanField(
        default=False,
        help_text='Show third party layer selector in Map screen'
    )

    enable_sass = models.BooleanField(
        default=False,
        help_text='Enable or disable SASS'
    )

    enable_download_request_approval = models.BooleanField(
        default=False,
        help_text=(
            'Download requests must be approved by the staff before they '
            'are sent to users'
        )
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
