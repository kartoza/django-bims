# coding=utf-8
"""
    Site Image model definition.
    To store images for location site.
"""

from django.db import models
from sass.models.site_visit import SiteVisit
from bims.models.survey import Survey


class SiteImage(models.Model):

    site = models.ForeignKey(
        'bims.LocationSite',
        null=False,
        blank=False,
        on_delete=models.CASCADE
    )

    image = models.ImageField(
        upload_to='site_images',
        null=False,
        blank=False
    )

    site_visit = models.ForeignKey(
        SiteVisit,
        null=True,
        blank=True,
        on_delete=models.SET_NULL
    )

    survey = models.ForeignKey(
        Survey,
        null=True,
        blank=True,
        on_delete=models.SET_NULL
    )
