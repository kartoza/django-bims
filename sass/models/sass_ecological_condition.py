# coding=utf-8
"""Sass ecological condition model definition.
"""
from django.contrib.gis.db import models


class SassEcologicalCondition(models.Model):
    ecoregion_level_1 = models.CharField(
        max_length=200,
        null=False,
        blank=False
    )

    geomorphological_zone = models.CharField(
        max_length=200,
        null=True,
        blank=True
    )

    ecological_category = models.ForeignKey(
        'sass.SassEcologicalCategory',
        null=True,
        blank=True
    )

    sass_score_precentile = models.IntegerField(
        null=True,
        blank=True
    )

    aspt_score_precentile = models.FloatField(
        null=True,
        blank=True
    )

