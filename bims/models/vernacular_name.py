# coding=utf-8
"""Vernacular name model definition.
"""

from django.db import models


class VernacularName(models.Model):

    name = models.CharField(
        null=False,
        blank=False,
        max_length=250
    )

    source = models.CharField(
        null=True,
        blank=True,
        max_length=250
    )

    language = models.CharField(
        null=True,
        blank=True,
        max_length=50
    )

    taxon_key = models.IntegerField(
        blank=True,
        null=True
    )

    def __str__(self):
        return self.name
