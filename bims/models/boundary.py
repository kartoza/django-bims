# coding=utf-8
"""Boundary model definition.
"""

from django.contrib.gis.db import models
from bims.models.boundary_type import BoundaryType


class Boundary(models.Model):
    """Boundary model."""

    name = models.CharField(
        max_length=128,
        blank=False,
    )
    type = models.ForeignKey(
        BoundaryType, on_delete=models.CASCADE
    )
    geometry = models.MultiPolygonField(blank=True, null=True)

    def __str__(self):
        return u'%s - %s' % (
            self.type, self.name)

    class Meta:
        unique_together = ("name", "type")
