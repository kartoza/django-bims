# coding=utf-8
"""Site visit model definition.
"""
from django.contrib.gis.db import models
from django.conf import settings
from django.utils import timezone
from django.contrib.postgres.fields import JSONField
from bims.models import LocationSite
from sass.enums.water_level import (
    WaterLevel,
    WATER_LEVEL_NAME,
)
from sass.enums.water_turbidity import WaterTurbidity
from sass.enums.canopy_cover import CanopyCover


class SiteVisit(models.Model):
    """Site visit model."""

    location_site = models.ForeignKey(
        LocationSite,
        on_delete=models.CASCADE,
        default=None
    )

    site_visit_date = models.DateField(
        default=timezone.now
    )

    assessor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True
    )

    water_level = models.CharField(
        max_length=100,
        choices=[
            (status.name, status.value[WATER_LEVEL_NAME])
            for status in WaterLevel],
        blank=True,
        null=True
    )

    water_turbidity = models.CharField(
        max_length=100,
        choices=[
            (status.name, status.value)
            for status in WaterTurbidity],
        blank=True,
        null=True
    )

    canopy_cover = models.CharField(
        max_length=100,
        choices=[
            (status.name, status.value)
            for status in CanopyCover],
        blank=True,
        null=True
    )

    average_velocity = models.IntegerField(
        null=True,
        blank=True
    )

    average_depth = models.IntegerField(
        null=True,
        blank=True
    )

    discharge = models.IntegerField(
        null=True,
        blank=True
    )

    sass_version = models.IntegerField(
        null=True,
        blank=True
    )

    sass_biotope_fraction = models.ManyToManyField(
        'sass.SassBiotopeFraction',
        null=True,
        blank=True
    )

    additional_data = JSONField(
        null=True,
        blank=True,
        default={}
    )
