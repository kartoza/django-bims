# coding=utf-8
"""Carousel header model definition.

"""

from django.db import models


class CarouselHeader(models.Model):
    """Carousel header model."""

    banner = models.ImageField(
        upload_to='banner'
    )

    description = models.TextField(
        blank=True,
        default='',
    )
