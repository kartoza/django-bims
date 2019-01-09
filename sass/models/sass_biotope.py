# coding=utf-8
"""Sass biotope model definition.
"""
from django.contrib.gis.db import models
from django.contrib.postgres.fields import JSONField


class SassBiotope(models.Model):
    """Sass Biotope model."""
    BIOTOPE_FORM_CHOICES = (
        ('0', '0'),
        ('1', '1'),
        ('2', '2')
    )

    name = models.CharField(
        max_length=200,
        blank=False,
    )

    description = models.TextField(
        null=True,
        blank=True
    )

    display_order = models.FloatField(
        null=True,
        blank=True
    )

    biotope_form = models.CharField(
        max_length=2,
        choices=BIOTOPE_FORM_CHOICES,
        blank=True,
    )

    additional_data = JSONField(
        default={},
        null=True,
        blank=True
    )

    def __unicode__(self):
        return self.name
