from django.contrib.gis.db import models


class SpatialScaleGroup(models.Model):

    name = models.CharField(
        max_length=200,
        null=False,
        blank=False
    )

    key = models.CharField(
        max_length=200,
        null=True,
        blank=True
    )

    parent = models.ForeignKey(
        verbose_name='Parent',
        to='self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    def __unicode__(self):
        return self.name
