from django.contrib.gis.db import models
from sass.enums.chem_unit import ChemUnit


class Unit(models.Model):

    unit = models.CharField(
        max_length=200,
        blank=True,
        null=True
    )

    unit_name = models.CharField(
        max_length=200,
        blank=True,
        null=True
    )

    def __str__(self):
        return self.unit

    def __unicode__(self):
        return self.unit

    class Meta:
        verbose_name_plural = "Units"
        verbose_name = "Unit"


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

    decimal_place = models.IntegerField(
        null=True,
        blank=True
    )

    minimum = models.FloatField(
        null=True,
        blank=True
    )

    maximum = models.FloatField(
        null=True,
        blank=True
    )

    show_in_abiotic_list = models.BooleanField(
        default=False
    )

    chem_unit = models.ForeignKey(Unit, null=True, on_delete=models.CASCADE)

    def __str__(self):
        return self.chem_code

    def __unicode__(self):
        return self.chem_code

    class Meta:
        verbose_name_plural = "Chemistry units"
        verbose_name = "Chemistry unit"

