# coding=utf-8
"""Taxon group model definition.

"""
from django.contrib.gis.db import models
from bims.enums.taxonomic_group_category import TaxonomicGroupCategory


class TaxonGroup(models.Model):

    CHART_CHOICES = (
        ('conservation status', 'Conservation Status'),
        ('division', 'Division'),
        ('sass', 'SASS'),
        ('origin', 'Origin'),
        ('endemism', 'Endemism'),
    )

    name = models.CharField(
        max_length=200,
        null=False,
        blank=False
    )

    singular_name = models.CharField(
        max_length=200,
        null=True,
        blank=True
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

    taxonomies = models.ManyToManyField(
        'bims.Taxonomy',
        blank=True
    )

    source_collection = models.CharField(
        help_text='Additional filter for search collections',
        max_length=200,
        null=True,
        blank=True
    )

    display_order = models.IntegerField(
        null=True,
        blank=True
    )

    chart_data = models.CharField(
        help_text='Data to display on chart',
        max_length=100,
        choices=CHART_CHOICES,
        null=True,
        blank=True,
        default=''
    )

    class Meta:
        ordering = ('display_order',)

    def __unicode__(self):
        return self.name

    def __str__(self):
        return self.name
