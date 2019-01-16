# coding=utf-8
"""Rate model definition.
"""
from django.contrib.gis.db import models


class Rate(models.Model):
    """Rate model."""

    rate = models.IntegerField(
        blank=False,
        null=False
    )

    description = models.CharField(
        max_length=200,
        null=True,
        blank=True
    )

    group = models.IntegerField(
        blank=True,
        null=True
    )

    def __unicode__(self):
        if self.description:
            return self.description
        else:
            return str(self.rate)
