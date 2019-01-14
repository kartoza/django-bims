from django.contrib.gis.db import models
from sass.models.abstract_additional_data import AbstractAdditionalData


class SassTaxon(AbstractAdditionalData):

    taxon = models.ForeignKey(
        'bims.taxonomy',
        on_delete=models.CASCADE,
        null=False,
        blank=False
    )

    taxon_sass_4 = models.CharField(
        max_length=200,
        blank=True,
        null=True
    )

    score = models.IntegerField(
        null=True,
        blank=True
    )

    sass_5_score = models.IntegerField(
        null=True,
        blank=True
    )

    air_breather = models.IntegerField(
        null=True,
        blank=True
    )

    display_order_sass_4 = models.IntegerField(
        null=True,
        blank=True
    )

    display_order_sass_5 = models.IntegerField(
        null=True,
        blank=True
    )

    def __unicode__(self):
        return self.taxon.scientific_name
