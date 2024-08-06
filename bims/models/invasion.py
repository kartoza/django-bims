from django.db import models
from ordered_model.models import OrderedModel


class Invasion(OrderedModel):
    category = models.CharField(
        blank=False,
    )

    description = models.TextField(
        default='',
        blank=True,
    )

    class Meta:
        app_label = 'bims'
        verbose_name_plural = 'Invasions'
        verbose_name = 'Invasion'
        ordering = ['order']

    def __str__(self):
        return self.category
