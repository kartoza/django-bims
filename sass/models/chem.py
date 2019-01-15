from django.contrib.gis.db import models
from sass.enums.chem_unit import ChemUnit


class Chem(models.Model):

    chem_code = models.CharField(
        max_length=100,
        null=False,
        blank=False
    )

    chem_description = models.CharField(
        max_length=200,
        null=True,
        blank=True
    )

    chem_unit = models.CharField(
        max_length=200,
        choices=[
            (status.name, status.value)
            for status in ChemUnit],
        blank=True,
        null=True
    )

    minimum = models.FloatField(
        null=True,
        blank=True
    )

    maximum = models.FloatField(
        null=True,
        blank=True
    )

    def __unicode__(self):
        return self.chem_code
