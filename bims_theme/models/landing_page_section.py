# coding=utf-8
"""Landing page section model definition.

"""
from colorfield.fields import ColorField
from django.db import models
from ordered_model.models import OrderedModel


class LandingPageSection(OrderedModel):
    """Landing page section model."""
    name = models.CharField(
        max_length=255,
        null=False,
        blank=False,
        help_text=(
            'Name of the section, for identifier only, '
            'will not appear in landing page'
        )
    )

    title = models.CharField(
        max_length=255,
        blank=True,
        default='',
        help_text='Title of the section, may be left blank'
    )

    contents = models.ManyToManyField(
        'bims_theme.LandingPageSectionContent',
        blank=True
    )

    background_color = ColorField(
        default='#FFFFFF',
        help_text='Background color for the section'
    )

    full_width = models.BooleanField(
        default=False,
        help_text='Enable this if you want the section to be full-width'
    )

    def __str__(self):
        return self.name
