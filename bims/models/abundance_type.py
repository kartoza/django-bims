# coding=utf-8
"""Abundance type model definition.

"""
from django.db import models
from ordered_model.models import OrderedModel


class AbundanceType(OrderedModel):
    name = models.CharField(
        max_length=256,
    )

    specific_module = models.ForeignKey(
        'bims.TaxonGroup',
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        help_text='If specified, then this abundance type will be available only for this module.'
    )

    def __str__(self):
        return self.name
