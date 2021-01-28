# coding=utf-8
"""Ingested data model definition.

"""
from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import fields


class IngestedData(models.Model):
    """Ingested data model
    """
    datetime = models.DateTimeField(
        auto_now_add=True,
        blank=True
    )

    is_valid = models.BooleanField(
        default=False
    )

    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE
    )

    object_id = models.PositiveIntegerField()
    content_object = fields.GenericForeignKey(
        'content_type',
        'object_id'
    )

    data_key = models.CharField(
        max_length=255,
        null=True,
        blank=True
    )

    category = models.TextField(
        null=True,
        blank=True
    )

    def __str__(self):
        return self.data_key if self.data_key else self.datetime

    class Meta:
        verbose_name_plural = 'Ingested data'
