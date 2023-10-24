# coding=utf-8
"""Sampling effort measure model definition.

"""
from django.db import models
from ordered_model.models import OrderedModel


class SamplingEffortMeasure(OrderedModel):
    name = models.CharField(
        max_length=256,
    )

    specific_module = models.ForeignKey(
        'bims.TaxonGroup',
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        help_text='If specified, then this sampling effort measure will be available only for this module.'
    )

    def __str__(self):
        return self.name
