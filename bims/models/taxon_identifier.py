from django.contrib.gis.db import models
from django.contrib.postgres.fields import ArrayField
from bims.enums.taxonomic_status import TaxonomicStatus
from bims.enums.taxonomic_rank import TaxonomicRank


class TaxonIdentifier(models.Model):

    gbif_key = models.IntegerField(
        verbose_name='GBIF Key',
        null=True,
        blank=True
    )

    scientific_name = models.CharField(
        verbose_name='Scientific Name',
        max_length=100,
        null=False,
        blank=False
    )

    canonical_name = models.CharField(
        verbose_name='Canonical Name',
        max_length=100,
        null=True,
        blank=True
    )

    rank = models.CharField(
        verbose_name='Taxonomic Rank',
        max_length=50,
        choices=[(rank.name, rank.value) for rank in TaxonomicRank],
        blank=True,
    )

    vernacular_names = ArrayField(
        models.CharField(
                max_length=100,
                blank=True,
                default=list),
        verbose_name='Vernacular Names',
        default=[],
        null=True,
        blank=True
    )

    taxonomic_status = models.CharField(
        verbose_name='Taxonomic Status',
        max_length=50,
        choices=[(status.name, status.value) for status in TaxonomicStatus],
        blank=True
    )

    parent = models.ForeignKey(
        verbose_name='Parent',
        to='self',
        on_delete=models.SET_NULL,
        null=True
    )

    def __unicode__(self):
        return '%s - %s' % (
            self.scientific_name,
            self.rank
        )

    def get_direct_children(self):
        children = TaxonIdentifier.objects.filter(
            parent=self
        )
        return children
