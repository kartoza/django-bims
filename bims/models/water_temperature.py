# coding=utf-8
"""Vernacular name model definition.
"""

from django.db import models
from django.conf import settings

from bims.models.location_site import LocationSite


class WaterTemperature(models.Model):

    date_time = models.DateTimeField(
        null=False,
        blank=False
    )

    location_site = models.ForeignKey(
        LocationSite,
        null=False,
        blank=False,
        on_delete=models.CASCADE
    )

    is_daily = models.BooleanField(
        default=False,
        help_text="Whether the data is daily or sub-daily."
    )

    value = models.FloatField(
        null=False,
        blank=False,
        help_text=(
          "Water temperature data, if daily data then this is the Mean value."
        )
    )

    minimum = models.FloatField(
        null=True,
        blank=True,
        help_text="This is for daily data"
    )

    maximum = models.FloatField(
        null=True,
        blank=True,
        help_text="This is for daily data"
    )

    uploader = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text='User who uploaded the data (Optional)',
        related_name='water_temperature_uploader'
    )

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text='Owner of the data (Optional)',
        related_name='water_temperature_owner'
    )

    source_file = models.CharField(
        default='',
        null=True,
        blank=True,
        help_text='Name of the source file',
        max_length=255
    )

    class Meta:
        ordering = ('-date_time', )
