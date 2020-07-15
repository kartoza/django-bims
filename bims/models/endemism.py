# coding=utf-8
"""Endemism model definition.

"""

from django.contrib.gis.db import models


class Endemism(models.Model):

    name = models.CharField(
        max_length=100,
        blank=False,
        null=False
    )

    description = models.TextField(
        blank=True,
        null=True
    )

    def __unicode__(self):
        return self.name

    def __str__(self):
        return self.name
