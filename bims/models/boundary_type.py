# coding=utf-8
"""Boundary model definition.
"""

from django.contrib.gis.db import models


class BoundaryType(models.Model):
    """Boundary type model."""

    name = models.CharField(
        max_length=128,
        blank=False,
        unique=True
    )

    def __str__(self):
        return u'%s' % self.name
