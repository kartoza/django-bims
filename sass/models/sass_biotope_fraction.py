# coding=utf-8
"""Sass biotope fraction model definition.
"""
from django.contrib.gis.db import models
from sass.models import Rate, SassBiotope


class SassBiotopeFraction(models.Model):
    """Sass biotope fraction biotope model."""

    sass_biotope = models.ForeignKey(
        SassBiotope,
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
        return '{rate} - {sass_biotope}'.format(
            rate=self.rate,
            sass_biotope=self.sass_biotope
        )
