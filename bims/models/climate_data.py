from django.db import models


class ClimateData(models.Model):

    title = models.CharField(
        max_length=256,
        null=False,
        blank=False
    )

    display_order = models.IntegerField(
        default=0
    )

    climate_geocontext_group_key = models.CharField(
        help_text='Geocontext group used for climate data',
        null=False,
        blank=False,
        max_length=128
    )

    class Meta:
        ordering = ('display_order', )

    def __str__(self):
        return self.title
