from django.contrib.gis.db import models
from bims.models.taxonomy import Taxonomy


class BioTaxon(models.Model):
    taxonomy = models.ForeignKey(
        Taxonomy,
        null=False,
        blank=False
    )

    bio_taxon_name = models.CharField(
        max_length=100,
        null=False,
        blank=False
    )

    note = models.TextField(
        null=True,
        blank=True
    )
