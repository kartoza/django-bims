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
    verified = models.BooleanField(
        default=False
    )
    layer_name = models.CharField(
        max_length=255,
        blank=True,
        default='',
        help_text='Name of the layer (for border)'
    )
    wms_url = models.CharField(
        max_length=255,
        blank=True,
        default='',
        help_text='WMS URL of the layer (for border)'
    )
    wms_format = models.CharField(
        max_length=255,
        blank=True,
        default='image/png',
        help_text='WMS format of the layer (for border)'
    )
    layer_identifier = models.CharField(
        max_length=255,
        blank=True,
        default='',
        help_text='Identifier to retrieve the desired value (for border)'
    )

    def __str__(self):
        return self.name
