# coding=utf-8
"""Boundary model definition.
"""

from django.contrib.gis.db import models
from django.db.models import Max


class BoundaryType(models.Model):
    """Boundary type model."""

    name = models.CharField(
        max_length=128,
        blank=False,
        unique=True
    )

    level = models.IntegerField(
        null=True,
        blank=True,
        help_text='what level of this boundary type'
    )

    def __str__(self):
        return u'%s' % self.name

    @staticmethod
    def lowest_type():
        lowest_level = BoundaryType.objects.all().aggregate(max=Max('level'))
        return BoundaryType.objects.get(
            level=lowest_level['max']
        )
