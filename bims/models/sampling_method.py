from django.contrib.gis.db import models
from bims.models.taxon_group import TaxonGroup


class SamplingMethodQuerySet(models.QuerySet):
    def sampling_method_list(self, taxon_group):
        if not isinstance(taxon_group, TaxonGroup):
            return []
        sampling_method_lower_list = []
        sampling_method_list = []
        sampling_methods = self.filter(
            taxon_group=taxon_group
        ).order_by('order')
        for sampling_method in sampling_methods:
            sampling_method_name = (
                sampling_method.sampling_method.replace('-', ' ')
            ).strip()
            if sampling_method_name.lower() not in sampling_method_lower_list:
                sampling_method_lower_list.append(sampling_method_name.lower())
                sampling_method_list.append(sampling_method)
        return sampling_method_list


class SamplingMethodManager(models.Manager):
    def get_queryset(self):
        return SamplingMethodQuerySet(self.model, using=self._db)

    def sampling_method_list(self, taxon_group):
        return self.get_queryset().sampling_method_list(
            taxon_group
        )


class SamplingMethod(models.Model):
    """Sampling method model definition"""

    objects = SamplingMethodManager()

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

    order = models.IntegerField(
        null=True,
        blank=True
    )

    def __unicode__(self):
        return self.sampling_method

    def __str__(self):
        return self.sampling_method
