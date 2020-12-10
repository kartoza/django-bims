# coding=utf-8
"""Basemap layer model definition.
"""

from django.db import models
from django.contrib.postgres.fields import JSONField
from django.db.models.signals import post_save
from django.dispatch import receiver
from ordered_model.models import OrderedModel


class BaseMapLayer(OrderedModel):
    """Base map layer model."""
    SOURCE_TYPE_CHOICES = (
        ('xyz', 'XYZ'),
        ('bing', 'BingMaps'),
        ('osm', 'OSM'),
        ('stamen', 'Stamen')
    )
    title = models.CharField(
        max_length=256,
        unique=True
    )
    source_type = models.CharField(
        max_length=100,
        choices=SOURCE_TYPE_CHOICES
    )
    layer_name = models.CharField(
        max_length=100,
        default='',
        blank=True,
        help_text='Only for Stamen base layer'
    )
    attributions = models.TextField(
        default='',
        blank=True
    )
    url = models.URLField(
        null=True,
        blank=True
    )
    key = models.CharField(
        max_length=256,
        default='',
        blank=True,
        help_text=(
            'Key is required if the source of the map is Bing'
        )
    )
    additional_params = JSONField(
        blank=True,
        null=True
    )
    default_basemap = models.BooleanField(
        default=False
    )

    # noinspection PyClassicStyleClass
    class Meta:
        """Meta class for project."""
        app_label = 'bims'
        ordering = ('order',)

    def __str__(self):
        return self.title


@receiver(post_save, sender=BaseMapLayer)
def disable_others(sender, instance, **kwargs):
    if instance.default_basemap:
        BaseMapLayer.objects.exclude(pk=instance.pk).update(
            default_basemap=False)
