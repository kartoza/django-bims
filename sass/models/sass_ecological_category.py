# coding=utf-8
"""Sass ecological category model definition.
"""
from django.contrib.gis.db import models
from colorfield.fields import ColorField


class SassEcologicalCategory(models.Model):
    """Ecological category model for interpreting SASS data."""

    category = models.CharField(
        max_length=10,
        null=False,
        blank=False
    )

    name = models.CharField(
        max_length=100,
        null=True,
        blank=True
    )

    description = models.CharField(
        max_length=255,
        null=True,
        blank=True
    )

    colour = ColorField(default='#009106')

    order = models.IntegerField(
        null=True,
        blank=True
    )

    def __unicode__(self):
        return self.category
