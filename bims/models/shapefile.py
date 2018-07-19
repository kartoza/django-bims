# coding=utf-8
"""Shapefile document model definition.

"""

from django.db import models


class Shapefile(models.Model):
    """Shapefile model
    """
    shapefile = models.FileField(upload_to='shapefile/')

    token = models.CharField(
            max_length=100,
            null=True,
            blank=True
    )

    @property
    def filename(self):
        return self.shapefile.name

    @property
    def fileurl(self):
        return self.shapefile.url

    # noinspection PyClassicStyleClass
    class Meta:
        """Meta class for project."""
        app_label = 'bims'
        verbose_name_plural = 'Shapefiles'
        verbose_name = 'Shapefile'
