# coding=utf-8
"""Taxon extra attribute model definition

"""

from django.db import models

from bims.models.taxon_group import TaxonGroup


class TaxonExtraAttribute(models.Model):
    name = models.CharField(
        max_length=255,
        null=False,
        blank=False
    )

    taxon_group = models.ForeignKey(
        TaxonGroup,
        null=False,
        blank=False,
        on_delete=models.CASCADE
    )

    class Meta:
        ordering = ('name', )
