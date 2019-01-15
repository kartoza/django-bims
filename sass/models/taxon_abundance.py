from django.contrib.gis.db import models


class TaxonAbundance(models.Model):

    abc = models.CharField(
        max_length=10,
        null=True,
        blank=True
    )

    description = models.CharField(
        max_length=200,
        null=True,
        blank=True
    )

    display_order = models.IntegerField(
        null=True,
        blank=True
    )

    def __unicode__(self):
        return '{abc} - {description}'.format(
            abc=self.abc,
            description=self.description
        )
