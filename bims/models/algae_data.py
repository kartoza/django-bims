# coding=utf-8
"""Model for algae data, it has a reference to biological_collection_record

"""

from django.db import models


class AlgaeData(models.Model):

    biological_collection_record = models.ForeignKey(
        'bims.BiologicalCollectionRecord',
        null=False,
        blank=False,
        related_name='algae_data'
    )

    curation_process = models.CharField(
        max_length=100,
        null=True,
        blank=True
    )

    indicator_chl_a = models.CharField(
        max_length=100,
        blank=True,
        default='',
        verbose_name='Biomass Indicator: Chl A'
    )

    chl_a = models.FloatField(
        null=True,
        blank=True,
        verbose_name='Chlorophyll a: benthic'
    )

    indicator_asdm = models.CharField(
        max_length=100,
        blank=True,
        default='',
        verbose_name='Biomass Indicator: Ash Free Dry Mass'
    )

    asdm = models.FloatField(
        null=True,
        blank=True,
        verbose_name='Ash Free Dry Mass'
    )

    ai = models.FloatField(
        null=True,
        blank=True,
        verbose_name='Autotrophic Index (AI)'
    )

    class Meta:
        verbose_name_plural = 'Algae data'
        verbose_name = 'Algae data'
