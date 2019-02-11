from django.contrib.gis.db import models
from bims.models import BiologicalCollectionRecord
from sass.models import SiteVisit, TaxonAbundance


class SiteVisitTaxon(BiologicalCollectionRecord):
    site_visit = models.ForeignKey(
        SiteVisit,
        on_delete=models.CASCADE,
        null=False,
        blank=False
    )

    taxon_abundance = models.ForeignKey(
        TaxonAbundance,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    sass_taxon = models.ForeignKey(
        'sass.SassTaxon',
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
