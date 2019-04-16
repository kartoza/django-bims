from django.db import models
from django.dispatch import receiver

from bims.enums.taxonomic_status import TaxonomicStatus
from bims.enums.taxonomic_rank import TaxonomicRank
from bims.models.iucn_status import IUCNStatus
from bims.models.endemism import Endemism
from bims.utils.iucn import get_iucn_status
from bims.permissions.generate_permission import generate_permission
from bims.models.document_links_mixin import DocumentLinksMixin
from bims.models.vernacular_name import VernacularName


class Taxonomy(DocumentLinksMixin):

    gbif_key = models.IntegerField(
        verbose_name='GBIF Key',
        null=True,
        blank=True
    )

    scientific_name = models.CharField(
        verbose_name='Scientific Name',
        max_length=200,
        null=False,
        blank=False
    )

    canonical_name = models.CharField(
        verbose_name='Canonical Name',
        max_length=200,
        null=True,
        blank=True
    )

    rank = models.CharField(
        verbose_name='Taxonomic Rank',
        max_length=50,
        choices=[(rank.name, rank.value) for rank in TaxonomicRank],
        blank=True,
    )

    vernacular_names = models.ManyToManyField(
        to=VernacularName,
        blank=True,
        null=True,
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
        null=True,
        blank=True
    )

    iucn_status = models.ForeignKey(
        IUCNStatus,
        models.SET_NULL,
        verbose_name='IUCN status',
        null=True,
        blank=True,
    )

    iucn_redlist_id = models.IntegerField(
        verbose_name='IUCN taxon id',
        null=True,
        blank=True
    )

    iucn_data = models.TextField(
        verbose_name='Data from IUCN',
        null=True,
        blank=True
    )

    endemism = models.ForeignKey(
        Endemism,
        models.SET_NULL,
        verbose_name='Endemism',
        null=True,
        blank=True
    )

    author = models.CharField(
        verbose_name='Author',
        max_length=200,
        null=True,
        blank=True
    )

    # noinspection PyClassicStyleClass
    class Meta:
        """Meta class for project."""
        app_label = 'bims'
        verbose_name_plural = 'Taxonomies'
        verbose_name = 'Taxonomy'

    def __unicode__(self):
        return '%s - %s' % (
            self.scientific_name,
            self.rank
        )

    def get_direct_children(self):
        children = Taxonomy.objects.filter(
            parent=self
        )
        return children

    def get_all_children(self):
        query = {}
        parent = ''
        or_condition = models.Q()
        for i in range(6):  # species to class
            parent += 'parent__'
            query[parent + 'in'] = [self]
        for key, value in query.items():
            or_condition |= models.Q(**{key: value})
        return Taxonomy.objects.filter(or_condition)

    @property
    def class_name(self):
        if self.rank != TaxonomicRank.CLASS.name and self.parent:
            return self.parent.class_name
        elif self.rank == TaxonomicRank.CLASS.name:
            return self.canonical_name
        return ''

    @property
    def phylum_name(self):
        if self.rank != TaxonomicRank.PHYLUM.name and self.parent:
            return self.parent.phylum_name
        elif self.rank == TaxonomicRank.PHYLUM.name:
            return self.canonical_name
        return ''

    @property
    def order_name(self):
        if self.rank != TaxonomicRank.ORDER.name and self.parent:
            return self.parent.order_name
        elif self.rank == TaxonomicRank.ORDER.name:
            return self.canonical_name
        return ''

    @property
    def family_name(self):
        if self.rank != TaxonomicRank.FAMILY.name and self.parent:
            return self.parent.family_name
        elif self.rank == TaxonomicRank.FAMILY.name:
            return self.canonical_name
        return ''

    @property
    def genus_name(self):
        if self.rank != TaxonomicRank.GENUS.name and self.parent:
            return self.parent.genus_name
        elif self.rank == TaxonomicRank.GENUS.name:
            return self.canonical_name
        return ''

    @property
    def is_species(self):
        return (
            self.rank == TaxonomicRank.SPECIES.name or
            self.rank == TaxonomicRank.SUBSPECIES.name
        )


@receiver(models.signals.pre_save, sender=Taxonomy)
def taxonomy_pre_save_handler(sender, instance, **kwargs):
    """Get iucn status before save."""
    if instance.rank == TaxonomicRank.CLASS.name:
        generate_permission(instance.scientific_name)

    if instance.is_species and not instance.iucn_status:
        iucn_status = get_iucn_status(
            species_name=instance.scientific_name
        )
        if iucn_status:
            instance.iucn_status = iucn_status
