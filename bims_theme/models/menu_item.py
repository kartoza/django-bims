# coding=utf-8
"""Landing page section model definition.

"""

from django.db import models
from ordered_model.models import OrderedModel


class MenuItem(OrderedModel):
    """Landing page section model."""
    title = models.CharField(
        max_length=255,
        null=False,
        blank=False,
        help_text=(
            'Menu item title'
        )
    )

    url = models.URLField()

    blank_target = models.BooleanField(
        default=False,
        help_text=(
            'Will open in a new tab'
        )
    )

    def __str__(self):
        return self.title
