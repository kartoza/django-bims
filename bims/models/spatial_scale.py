from django.contrib.gis.db import models

SPATIAL_SCALE_TYPE = (
    ('input', 'Input'),
    ('select', 'Select'),
)


class SpatialScale(models.Model):

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

    type = models.CharField(
        max_length=50,
        choices=SPATIAL_SCALE_TYPE,
        blank=False,
        null=False,
    )

    query = models.CharField(
        max_length=500,
        null=False,
        blank=False
    )

    group = models.ForeignKey(
        'bims.SpatialScaleGroup',
        null=False,
        blank=False
    )
