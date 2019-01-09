# coding=utf-8
"""
    Fbis uuid model definition.
    This model is used only for fbis data migration
    because they are using uuid for model id
"""

from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import fields


class FbisUUID(models.Model):

    uuid = models.CharField(
        null=False,
        blank=False,
        unique=False,
        max_length=50
    )
    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    content_object = fields.GenericForeignKey(
        'content_type',
        'object_id'
    )
