# coding=utf-8
"""Sass biotope fraction model definition.
"""
from django.contrib.gis.db import models
from sass.models import Rate


class SassBiotopeFraction(models.Model):
    """Sass biotope fraction biotope model."""

    sass_biotope = models.ForeignKey(
        'bims.biotope',
        on_delete=models.CASCADE,
        default=None,
        null=True,
        blank=True
    )

    rate = models.ForeignKey(
        Rate,
        on_delete=models.CASCADE,
        default=None,
        null=True,
        blank=True
    )

    def __unicode__(self):
        return '{rate} - {biotope}'.format(
            rate=self.rate,
            biotope=self.biotope
        )
