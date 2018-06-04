# coding=utf-8
"""Carousel header model definition.

"""

from django.db import models
from ordered_model.models import OrderedModel


class CarouselHeader(OrderedModel):
    """Carousel header model."""

    banner = models.ImageField(
        upload_to='banner'
    )

    description = models.TextField(
        blank=True,
        default='',
    )
