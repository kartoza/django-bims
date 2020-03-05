# coding=utf-8
"""Model for algae data, it has a reference to biological_collection_record

"""

from django.db import models


class AlgaeData(models.Model):

    survey = models.ForeignKey(
        'bims.Survey',
        null=True,
        blank=True,
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

    indicator_afdm = models.CharField(
        max_length=100,
        blank=True,
        default='',
        verbose_name='Biomass Indicator: Ash Free Dry Mass'
    )

    ai = models.FloatField(
        null=True,
        blank=True,
        verbose_name='Autotrophic Index (AI)'
    )

    class Meta:
        verbose_name_plural = 'Algae data'
        verbose_name = 'Algae data'
