from django.db import models
from ordered_model.models import OrderedModel


class TaxonOrigin(OrderedModel):
    category = models.CharField(
        blank=False,
    )

    origin_key = models.CharField(
        max_length=50,
        blank=True,
        default='',
    )

    description = models.TextField(
        default='',
        blank=True,
    )

    class Meta:
        app_label = 'bims'
        verbose_name_plural = 'Taxon Origins'
        verbose_name = 'Taxon Origin'
        ordering = ['order']

    def __str__(self):
        return self.category
