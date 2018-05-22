# coding=utf-8
"""Boundary model definition.
"""

from django.contrib.gis.db import models
from bims.models.boundary import Boundary


class Cluster(models.Model):
    """Cluster model.

    The cluster model creates pre-computer spatial cluster analysis for all
    sites and all record in a geographic region.
    The clustering is based on :
    - different geographical areas for different scales.
    - module of record based on biological_collection model. E.g. Fish.

    E.g. small scales will cluster by country, larger scale by province,
    catchment etc.
    The cluster units are configurable based on the boundary model.
    """
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
