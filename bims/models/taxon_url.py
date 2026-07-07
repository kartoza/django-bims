from django.db import models


class TaxonURL(models.Model):
    taxonomy = models.ForeignKey(
        'bims.Taxonomy',
        related_name='urls',
        on_delete=models.CASCADE,
    )
    uri = models.URLField(max_length=2000)
    label = models.CharField(max_length=255)

    class Meta:
        app_label = 'bims'
        ordering = ['label']
        verbose_name = 'Taxon URL'
        verbose_name_plural = 'Taxon URLs'

    def __str__(self):
        return f'{self.label} ({self.uri})'
