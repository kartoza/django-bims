from django.contrib.gis.db import models


class SassValidationStatus(models.Model):

    status = models.CharField(
        max_length=100,
        null=False,
        blank=False
    )

    colour = models.CharField(
        max_length=100,
        null=True,
        blank=True
    )

    colour_description = models.CharField(
        max_length=100,
        null=True,
        blank=True
    )

    missing_ind = models.IntegerField(
        null=True,
        blank=True
    )
