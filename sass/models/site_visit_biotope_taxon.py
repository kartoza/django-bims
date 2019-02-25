from django.contrib.gis.db import models
from django.utils import timezone


class SiteVisitBiotopeTaxon(models.Model):

    site_visit = models.ForeignKey(
        'sass.SiteVisit',
        on_delete=models.CASCADE,
        null=False,
        blank=False,
    )

    taxon = models.ForeignKey(
        'bims.Taxonomy',
        on_delete=models.CASCADE,
        null=False,
        blank=False
    )

    sass_taxon = models.ForeignKey(
        'sass.SassTaxon',
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )

    biotope = models.ForeignKey(
        'bims.Biotope',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    taxon_abundance = models.ForeignKey(
        'sass.TaxonAbundance',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    date = models.DateField(
        default=timezone.now
    )

    class Meta:
        verbose_name_plural = "Site visit biotope taxa"
