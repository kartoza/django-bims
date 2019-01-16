# coding=utf-8
"""River model definition.
"""
from django.contrib.gis.db import models
from django.conf import settings
from bims.models import AbstractValidation


class River(AbstractValidation):
    """River model."""

    name = models.CharField(
        max_length=128,
        blank=False,
    )

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True
    )

    @property
    def data_name(self):
        return self.name

    def __unicode__(self):
        return self.name
