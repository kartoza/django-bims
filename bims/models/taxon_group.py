# coding=utf-8
"""Taxon group model definition.

"""
from django.contrib.gis.db import models
from bims.models import Taxonomy
from bims.enums.taxonomic_group_category import TaxonomicGroupCategory


class TaxonGroup(models.Model):

    name = models.CharField(
        max_length=200,
        null=False,
        blank=False
    )

    category = models.CharField(
        verbose_name='Taxonomic Group Category',
        max_length=50,
        choices=[(rank.name, rank.value) for rank in TaxonomicGroupCategory],
        blank=True,
    )

    logo = models.ImageField(
        upload_to='module_logo',
        null=True,
        blank=True
    )

    taxonomies = models.ManyToManyField(Taxonomy)

    def __unicode__(self):
        return self.name
