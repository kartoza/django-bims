# -*- coding: utf-8 -*-

from django.db import models
from ordered_model.models import OrderedModel


class Partner(OrderedModel):

    name = models.CharField(
        max_length=128,
        blank=False,
        help_text='This will appear as a tooltip'
    )

    logo = models.ImageField(
        upload_to='partner_logo'
    )

    link = models.URLField(
        help_text=(
            'The url link for this partner, will make the logo clickable'
        ),
        max_length=200,
        null=True,
        blank=True
    )

    def __str__(self):
        return self.name
