# coding=utf-8
"""Non biodiversity layer model definition.
"""

from django.db import models
from ordered_model.models import OrderedModel


class NonBiodiversityLayer(OrderedModel):
    """Non biodiversity layer model."""
    name = models.CharField(
        max_length=100,
        unique=True
    )
    wms_url = models.CharField(
        max_length=256
    )
    wms_layer_name = models.CharField(
        max_length=128
    )
    wms_format = models.CharField(
        max_length=64,
        default='image/png'
    )
    layer_style = models.CharField(
        max_length=256,
        default='',
        help_text='Leave blank to use default style',
        blank=True
    )
    default_visibility = models.BooleanField(
        default=False
    )
    get_feature_format = models.TextField(
        max_length=100,
        default='text/plain'
    )

    # noinspection PyClassicStyleClass
    class Meta:
        """Meta class for project."""
        app_label = 'bims'
        ordering = ('order',)
