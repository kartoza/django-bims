from django.contrib.gis.db import models


class LocationContextGroup(models.Model):
    name = models.CharField(
        max_length=200,
        null=False,
        blank=False
    )
    key = models.CharField(
        max_length=100,
        blank=True,
        default=''
    )
    geocontext_group_key = models.CharField(
        max_length=255,
        blank=True,
        default='',
        help_text='Group key from geocontext'
    )
    layer_name = models.CharField(
        max_length=255,
        blank=True,
        default=''
    )

    def __str__(self):
        return self.name
