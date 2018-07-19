# coding=utf-8
"""Shapefile upload session model definition.

"""

from django.conf import settings
from django.utils import timezone
from django.db import models
from bims.models.shapefile import Shapefile


class ShapefileUploadSession(models.Model):
    """Shapefile upload session model
    """
    uploader = models.ForeignKey(
            settings.AUTH_USER_MODEL,
            models.SET_NULL,
            blank=True,
            null=True,
    )

    token = models.CharField(
            max_length=100,
            null=True,
            blank=True
    )

    uploaded_at = models.DateField(
            default=timezone.now
    )

    processed = models.BooleanField(
            default=False
    )

    error = models.TextField(
            blank=True,
            null=True
    )

    shapefiles = models.ManyToManyField(Shapefile)

    # noinspection PyClassicStyleClass
    class Meta:
        """Meta class for project."""
        app_label = 'bims'
        verbose_name_plural = 'Shapefile Upload Sessions'
        verbose_name = 'Shapefile Upload Session'
