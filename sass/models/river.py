# coding=utf-8
"""River model definition.
"""
from django.contrib.gis.db import models
from bims.models import AbstractValidation


class River(AbstractValidation):
    """River model."""

    name = models.CharField(
        max_length=128,
        blank=False,
    )

    @property
    def data_name(self):
        return self.name

    def __unicode__(self):
        return self.name
