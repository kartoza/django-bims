# coding=utf-8
"""Boundary model definition.
"""

from django.contrib.gis.db import models
from bims.models.boundary import Boundary


class BiologicalCollectionCluster(models.Model):
    """Biological Cluster model."""
    boundary = models.ForeignKey(
        Boundary,
        on_delete=models.CASCADE
    )
    module = models.CharField(
        max_length=128
    )
    site_count = models.IntegerField(default=0)
    survey_count = models.IntegerField(default=0)
    record_count = models.IntegerField(default=0)

    def __str__(self):
        return u'%s' % self.id

    class Meta:
        unique_together = (
            "boundary", "module")
