# coding=utf-8
"""Carousel header model definition.

"""

from django.db import models
from django.core.validators import MaxValueValidator, MinValueValidator
from ordered_model.models import OrderedModel
from colorfield.fields import ColorField


class CarouselHeader(OrderedModel):
    """Carousel header model."""
    ALIGNMENT_OPTIONS = [
        ('left', 'Left'),
        ('center', 'Center'),
        ('right', 'Right'),
        ('justify', 'Justify')
    ]

    STYLE_OPTIONS = [
        ('normal', 'Normal'),
        ('bold', 'Bold'),
        ('italic', 'Italic'),
    ]

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

    text_alignment = models.CharField(
        max_length=7,
        choices=ALIGNMENT_OPTIONS,
        default='left',
        help_text='Select the alignment for both title and description text.'
    )

    text_style = models.CharField(
        max_length=6,
        choices=STYLE_OPTIONS,
        default='normal',
        help_text='Choose the text style for the title and description.'
    )

    title_font_size = models.IntegerField(
        validators=[MinValueValidator(10), MaxValueValidator(80)],
        default=45,
        help_text='Specify the font size for the title. Value must be between 10 and 80.'
    )

    description_font_size = models.IntegerField(
        validators=[MinValueValidator(10), MaxValueValidator(50)],
        default=30,
        help_text='Specify the font size for the description. Value must be between 10 and 50.'
    )

    full_screen_background = models.BooleanField(default=False)

    class Meta:
        verbose_name_plural = 'Carousel Headers'
        ordering = ['order']

    def __str__(self):
        if self.title:
            return self.title
        if self.banner:
            return self.banner.name
        return 'Carousel Header - {}'.format(self.id)
