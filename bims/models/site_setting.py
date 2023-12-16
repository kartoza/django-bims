from django.db import models
from django.db.models import JSONField
from django.dispatch import receiver
from preferences.models import Preferences


class SiteSetting(Preferences):
    SITE_CODE_GENERATOR_CHOICES = (
        ('bims', 'BIMS (2 Site Name + 2 Site Description + Site count)'),
        ('fbis', 'FBIS (2 Secondary catchment + 4 River + Site count)'),
        (
            'rbis',
            'RBIS (Catchment + Province ID + District ID + Site count)'
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

    readme_download = models.FileField(
        null=True,
        blank=True,
        help_text='README that bundled with the downloaded occurrence data'
    )

    taxonomic_upload_template = models.FileField(
        null=True,
        blank=True,
        help_text=(
            'File template for taxonomic uploader'
        )
    )

    occurrence_upload_template = models.FileField(
        null=True,
        blank=True,
        help_text=(
            'File template for occurrence uploader'
        )
    )

    landing_page_occurrence_records_title = models.CharField(
        default='BIODIVERSITY OCCURRENCE RECORDS',
        help_text=(
            'Header title for Biodiversity Occurrence Records section in '
            'landing page'
        ),
        max_length=150
    )

    landing_page_partners_title = models.CharField(
        default='PARTNERS',
        help_text='Header title for Partners section in landing page',
        max_length=150
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

    recaptcha_site_key = models.CharField(
        default='',
        max_length=150
    )

    recaptcha_secret_key = models.CharField(
        default='',
        max_length=150
    )

    iucn_api_key = models.CharField(
        max_length=255,
        default='',
        help_text=(
            'Token key for IUCN api'
        )
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

    enable_water_temperature = models.BooleanField(
        default=False,
        help_text='Enable or disable Water Temperature data'
    )

    enable_download_request_approval = models.BooleanField(
        default=False,
        help_text=(
            'Download requests must be approved by the staff before they '
            'are sent to users'
        )
    )

    show_module_summary_on_dashboard = models.BooleanField(
        default=False,
        help_text=(
            'Show summative figure for data by taxon group'
        )
    )

    enable_remove_all_occurrences_tool = models.BooleanField(
        default=False,
        help_text=(
            'Enable tool to remove all occurrences for a taxon group'
        )
    )

    github_repo_path = models.CharField(
        default='',
        blank=True,
        max_length=255,
        help_text=(
            'Path to git repository from where the version info can be '
            'retrieved'
        )
    )

    boundary_key = models.CharField(
        max_length=100,
        blank=True,
        default='',
        help_text='The key of the boundary data form GeoContext'
    )

    copyright_text = models.CharField(
        max_length=200,
        blank=True,
        default='Copyright © Kartoza'
    )

    pesticide_quaternary_data_file = models.FileField(
        null=True,
        blank=True,
        help_text=(
            'File containing pesticide data per quaternary. '
            'If not provided, the pesticide dashboard will be unavailable.'
        )
    )
