# coding=utf-8
"""Chart color model definition."""

from django.db import models


class ChartColor(models.Model):
    """Model for storing chart colors that can be used across the application."""

    color = models.CharField(
        max_length=7,
        help_text='Hex color code (e.g., #FF5733)'
    )

    order = models.IntegerField(
        default=0,
        help_text='Order of the color in the palette'
    )

    class Meta:
        ordering = ['order']
        verbose_name = 'Chart Color'
        verbose_name_plural = 'Chart Colors'

    def __str__(self):
        return f'{self.color} (Order: {self.order})'
