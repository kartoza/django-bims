from django.db import models
from preferences.models import Preferences


class GeocontextSetting(Preferences):
    geocontext_url = models.URLField(
        blank=True,
        default='https://geocontext.kartoza.com/',
        help_text='Full URL for GeoContext service '
                  '(include http:// and ends with /).'
    )

    geocontext_keys = models.TextField(
        verbose_name='Geocontext Group Keys',
        help_text='Geocontext group keys that will be fetched '
                  'from Geocontext, separated by commas.',
        default='provinces,rainfall_group',
        blank=True
    )

    tolerance = models.FloatField(
        default=0.0,
        help_text='The radius tolerance for the spatial query'
    )
