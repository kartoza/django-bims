# coding=utf-8
"""User boundary model definition.
"""
from django.conf import settings
from django.contrib.gis.db import models


class UserBoundary(models.Model):
    """User Boundary model."""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )

    name = models.CharField(
        max_length=128,
        blank=False,
    )

    geometry = models.MultiPolygonField(
        blank=False,
        null=False
    )

    def __str__(self):
        return u'%s' % self.name
