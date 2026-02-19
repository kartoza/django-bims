from django.db import models


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
        default=False,
        db_index=True
    )

    is_rejected = models.BooleanField(
        default=False,
        db_index=True
    )

    endemism = models.ForeignKey(
        'bims.Endemism',
        models.SET_NULL,
        verbose_name='Endemism',
        null=True,
        blank=True
    )

    origin = models.ForeignKey(
        'bims.TaxonOrigin',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        help_text='Origin'
    )

    class Meta:
        unique_together = ('taxongroup', 'taxonomy')
