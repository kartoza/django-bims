# coding=utf-8
"""Taxon group model definition.

"""
from django.contrib.gis.db import models
from bims.models import TaxonIdentifier


class TaxonGroup(models.Model):

    name = models.CharField(
        max_length=200,
        null=False,
        blank=False
    )

    taxon_identifiers = models.ManyToManyField(TaxonIdentifier)

    def __unicode__(self):
        return self.name
