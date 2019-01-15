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
