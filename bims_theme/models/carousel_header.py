# coding=utf-8
"""Carousel header model definition.

"""

from django.db import models
from django.core.validators import MaxValueValidator, MinValueValidator
from ordered_model.models import OrderedModel
from colorfield.fields import ColorField


class CarouselHeader(OrderedModel):
    """Carousel header model."""

    banner = models.ImageField(
        upload_to='banner'
    )

    title = models.TextField(
        blank=True,
        default='',
        help_text='Title of the carousel'
    )

    description = models.TextField(
        blank=True,
        default='',
        verbose_name='Paragraph',
        help_text='Paragraph inside carousel'
    )

    text_color = ColorField(
        default='#FFFFFF',
        help_text='Color of the text inside carousel'
    )

    background_color_overlay = ColorField(
        default='#FFFFFF',
        help_text='Background color overlay behind the text'
    )

    background_overlay_opacity = models.PositiveIntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text='Opacity of the background overlay, in percentage'
    )

    class Meta:
        verbose_name_plural = 'Carousel Headers'
        ordering = ['order']

    def __str__(self):
        if self.title:
            return self.title
        if self.banner:
            return self.banner.name
        return 'Carousel Header - {}'.format(self.id)
