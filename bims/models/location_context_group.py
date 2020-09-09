from django.contrib.gis.db import models
from django.dispatch import receiver
from django.db.models.signals import post_save


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


@receiver(post_save, sender=LocationContextGroup)
def location_context_group_post_save(**kwargs):
    from bims.tasks.location_context import generate_spatial_scale_filter
    import os
    from django.conf import settings
    file_name = 'spatial_scale_filter_list.txt'
    file_path = os.path.join(
        settings.MEDIA_ROOT,
        file_name
    )
    generate_spatial_scale_filter.delay(file_path)
