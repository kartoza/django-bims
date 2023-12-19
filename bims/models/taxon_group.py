# coding=utf-8
"""Taxon group model definition.

"""
from django.contrib.gis.db import models
from django.contrib.sites.models import Site
from django.dispatch import receiver

from bims.enums.taxonomic_group_category import TaxonomicGroupCategory
from bims.tasks.collection_record import (
    assign_site_to_uncategorized_records
)


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

    site = models.ForeignKey(
        Site,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name="Associated Site",
        help_text="The site this taxon group is associated with."
    )

    class Meta:
        ordering = ('display_order',)

    def __unicode__(self):
        return self.name

    def __str__(self):
        return self.name


@receiver(models.signals.post_save)
def taxon_group_post_save(sender, instance, created, **kwargs):
    if not issubclass(sender, TaxonGroup):
        return

    if not instance.site:
        return

    assign_site_to_uncategorized_records.delay(
        instance.id, instance.site_id
    )
