from django.db import models
from bims.models.taxonomy import Taxonomy


class TaxonGroupTaxonomy(models.Model):
    taxongroup = models.ForeignKey(
        'bims.TaxonGroup',
        on_delete=models.CASCADE,
    )

    taxonomy = models.ForeignKey(
        'bims.Taxonomy',
        on_delete=models.CASCADE,
    )

    is_validated = models.BooleanField(
        default=False
    )

    endemism = models.ForeignKey(
        'bims.Endemism',
        models.SET_NULL,
        verbose_name='Endemism',
        null=True,
        blank=True
    )

    origin = models.CharField(
        max_length=50,
        choices=Taxonomy.CATEGORY_CHOICES,
        blank=True,
        default='',
        help_text='Origin'
    )

    class Meta:
        unique_together = ('taxongroup', 'taxonomy')
