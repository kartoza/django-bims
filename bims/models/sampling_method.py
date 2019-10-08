from django.contrib.gis.db import models


class SamplingMethod(models.Model):
    """Sampling method model definition"""

    sampling_method = models.CharField(
        max_length=200,
        null=False,
        blank=False
    )

    effort_measure = models.CharField(
        max_length=300,
        null=True,
        blank=True
    )

    normalisation_factor = models.IntegerField(
        null=True,
        blank=True
    )

    factor_description = models.CharField(
        max_length=300,
        null=True,
        blank=True
    )

    comment = models.TextField(
        null=True,
        blank=True
    )

    taxon_group = models.ManyToManyField(
        'bims.TaxonGroup',
        null=True,
        blank=True
    )

    def __unicode__(self):
        return self.sampling_method
