import json
from django.db import models
from django.dispatch import receiver
from django.utils import timezone

from bims.enums.taxonomic_status import TaxonomicStatus
from bims.enums.taxonomic_rank import TaxonomicRank
from bims.models.iucn_status import IUCNStatus
from bims.models.endemism import Endemism
from bims.utils.iucn import get_iucn_status
from bims.permissions.generate_permission import generate_permission
from bims.models.vernacular_name import VernacularName
from django.contrib.postgres.fields import JSONField

ORIGIN_CATEGORIES = {
    'non-native': 'alien',
    'native': 'indigenous',
    'unknown': 'unknown',
    'non-native: invasive': 'alien-invasive',
    'non-native: non-invasive': 'alien-non-invasive'
}


class TaxonomyField(models.CharField):

    description = 'A taxonomy field.'

    def __init__(self, taxonomy_key=None, *args, **kwargs):
        kwargs['max_length'] = 100
        kwargs['blank'] = True
        kwargs['default'] = ''
        self.taxonomy_key = taxonomy_key
        super(TaxonomyField, self).__init__(*args, **kwargs)


class Taxonomy(models.Model):
    CATEGORY_CHOICES = (
        (ORIGIN_CATEGORIES['non-native'], 'Non-Native'),
        (ORIGIN_CATEGORIES['native'], 'Native'),
        (ORIGIN_CATEGORIES['unknown'], 'Unknown'),
        (ORIGIN_CATEGORIES['non-native: invasive'], 'Non-native: invasive'),
        (
            ORIGIN_CATEGORIES['non-native: non-invasive'],
            'Non-native: non-invasive'
        )
    )

    gbif_key = models.IntegerField(
        verbose_name='GBIF Key',
        null=True,
        blank=True
    )

    verified = models.BooleanField(
        help_text='The data has been verified',
        default=False
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

    legacy_canonical_name = models.CharField(
        verbose_name='Legacy Canonical Name',
        max_length=700,
        blank=True,
        default=''
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

    origin = models.CharField(
        max_length=50,
        choices=CATEGORY_CHOICES,
        blank=True,
        default='',
        help_text='Origin'
    )

    author = models.CharField(
        verbose_name='Author',
        max_length=200,
        null=True,
        blank=True
    )

    gbif_data = JSONField(
        verbose_name='Json data from gbif',
        null=True,
        blank=True
    )

    additional_data = JSONField(
        verbose_name='Additional json data',
        null=True,
        blank=True
    )

    import_date = models.DateField(
        default=timezone.now,
        blank=True,
        null=True,
    )

    def save_json_data(self, json_field):
        max_allowed = 10
        attempt = 0
        is_dictionary = False
        json_data = {}
        if not json_field:
            return json_data
        while not is_dictionary and attempt < max_allowed:
            if not json_field:
                break
            if isinstance(json_field, dict):
                is_dictionary = True
                json_data = json_field
            else:
                json_data = json.loads(json_field)
                attempt += 1
        return json_data

    def save(self, *args, **kwargs):
        if self.gbif_data:
            self.gbif_data = self.save_json_data(self.gbif_data)
        if self.additional_data:
            self.additional_data = self.save_json_data(self.additional_data)
        super(Taxonomy, self).save(*args, **kwargs)

    # noinspection PyClassicStyleClass
    class Meta:
        """Meta class for project."""
        app_label = 'bims'
        verbose_name_plural = 'Taxa'
        verbose_name = 'Taxonomy'

    def __unicode__(self):
        return '%s - %s' % (
            self.scientific_name,
            self.rank
        )

    def __str__(self):
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

    def parent_by_rank(self, rank):
        taxon = self
        current_rank = taxon.rank
        while current_rank != rank and taxon.parent:
            taxon = taxon.parent
            current_rank = taxon.rank
        if current_rank == rank:
            return taxon
        return None

    @property
    def taxon_class(self):
        if self.rank != TaxonomicRank.CLASS.name and self.parent:
            return self.parent.taxon_class
        if self.rank == TaxonomicRank.CLASS.name:
            return self
        return None

    @property
    def class_name(self):
        if self.rank != TaxonomicRank.CLASS.name and self.parent:
            return self.parent.class_name
        elif self.rank == TaxonomicRank.CLASS.name:
            return self.canonical_name
        return ''

    @property
    def kingdom_name(self):
        if self.rank != TaxonomicRank.KINGDOM.name and self.parent:
            return self.parent.kingdom_name
        elif self.rank == TaxonomicRank.KINGDOM.name:
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
    def species_name(self):
        if self.rank != TaxonomicRank.SPECIES.name and self.parent:
            return self.parent.species_name
        elif self.rank == TaxonomicRank.SPECIES.name:
            return self.canonical_name
        return ''

    @property
    def is_species(self):
        return (
            self.rank == TaxonomicRank.SPECIES.name or
            self.rank == TaxonomicRank.SUBSPECIES.name
        )

    @property
    def name(self):
        if self.canonical_name:
            return self.canonical_name
        elif self.scientific_name:
            return self.scientific_name
        return '-'


@receiver(models.signals.pre_save, sender=Taxonomy)
def taxonomy_pre_save_handler(sender, instance, **kwargs):
    """Get iucn status before save."""
    if instance.rank == TaxonomicRank.CLASS.name:
        generate_permission(instance.scientific_name)

    if instance.is_species and not instance.iucn_status:
        iucn_status = get_iucn_status(
            species_name=instance.canonical_name,
            only_returns_json=True
        )
        if iucn_status and 'result' in iucn_status:
            if len(iucn_status['result']) > 0:
                iucn, _ = IUCNStatus.objects.get_or_create(
                    category=iucn_status['result'][0]['category']
                )
                instance.iucn_status = iucn
                instance.iucn_redlist_id = iucn_status['result'][0]['taxonid']
                instance.iucn_data = json.dumps(
                    iucn_status['result'][0],
                    indent=4)
            else:
                iucn_status = None
        if not iucn_status:
            # Get not evaluated
            try:
                iucn_status, _ = IUCNStatus.objects.get_or_create(
                    category='NE'
                )
            except IUCNStatus.MultipleObjectsReturned:
                iucn_status = IUCNStatus.objects.filter(
                    category='NE'
                )[0]
            instance.iucn_status = iucn_status


class TaxonImage(models.Model):

    taxon_image = models.ImageField(
        upload_to='taxon_images',
        null=True,
        blank=True
    )
    taxonomy = models.ForeignKey(
        Taxonomy, on_delete=models.CASCADE
    )
