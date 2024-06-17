import json

from django.conf import settings
from django.contrib.sites.models import Site
from django.core.mail.message import EmailMultiAlternatives
from django.template.loader import render_to_string
from taggit.managers import TaggableManager

from bims.models.validation import AbstractValidation
from django.db import models
from django.dispatch import receiver
from django.utils import timezone

from bims.enums.taxonomic_status import TaxonomicStatus
from bims.enums.taxonomic_rank import TaxonomicRank
from bims.models.iucn_status import IUCNStatus
from bims.models.endemism import Endemism
from bims.utils.iucn import get_iucn_status
from bims.models.vernacular_name import VernacularName
from bims.models.notification import (
    get_recipients_for_notification,
    NEW_TAXONOMY
)
from django.db.models import JSONField

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


class Taxonomy(AbstractValidation):

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
    CATEGORY_CHOICES_DICT = {
        ORIGIN_CATEGORIES['non-native']: 'Non-Native',
        ORIGIN_CATEGORIES['native']: 'Native',
        ORIGIN_CATEGORIES['unknown']: 'Unknown',
        ORIGIN_CATEGORIES['non-native: invasive']: 'Non-native: invasive',
        ORIGIN_CATEGORIES['non-native: non-invasive']: 'Non-native: non-invasive'
    }
    tags = TaggableManager(
        blank=True,
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

    national_conservation_status = models.ForeignKey(
        IUCNStatus,
        models.SET_NULL,
        related_name='national_conservation_status',
        verbose_name='National Conservation Status',
        null=True,
        blank=True,
    )

    iucn_status = models.ForeignKey(
        IUCNStatus,
        models.SET_NULL,
        verbose_name='Global Red List Status (IUCN)',
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

    accepted_taxonomy = models.ForeignKey(
        related_name='synonym',
        to='self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
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
        update_taxon_with_gbif = False
        if self.gbif_data:
            self.gbif_data = self.save_json_data(self.gbif_data)
        if self.additional_data:
            self.additional_data = self.save_json_data(self.additional_data)
        if self.additional_data and 'fetch_gbif' in self.additional_data:
            update_taxon_with_gbif = True
            del self.additional_data['fetch_gbif']
        super(Taxonomy, self).save(*args, **kwargs)

        if update_taxon_with_gbif:
            from bims.utils.fetch_gbif import fetch_all_species_from_gbif
            fetch_all_species_from_gbif(
                species=self.scientific_name,
                parent=self.parent,
                gbif_key=self.gbif_key,
                fetch_vernacular_names=True)

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
    def data_name(self):
        return self.canonical_name

    @property
    def taxon_class(self):
        if self.rank != TaxonomicRank.CLASS.name and self.parent:
            return self.parent.taxon_class
        if self.rank == TaxonomicRank.CLASS.name:
            return self
        return None

    def get_taxon_rank_name(self, rank):
        limit = 20
        current_try = 0
        _taxon = self
        _parent = _taxon.parent
        _rank = _taxon.rank
        while (
                _parent and _rank
                and _rank != rank
                and current_try < limit
        ):
            current_try += 1
            _taxon = _parent
            _rank = _taxon.rank
            _parent = _taxon.parent

        if _rank == rank:
            return _taxon.canonical_name
        return ''

    @property
    def class_name(self):
        return self.get_taxon_rank_name(TaxonomicRank.CLASS.name)

    @property
    def kingdom_name(self):
        return self.get_taxon_rank_name(TaxonomicRank.KINGDOM.name)

    @property
    def phylum_name(self):
        return self.get_taxon_rank_name(TaxonomicRank.PHYLUM.name)

    @property
    def order_name(self):
        return self.get_taxon_rank_name(TaxonomicRank.ORDER.name)

    @property
    def family_name(self):
        return self.get_taxon_rank_name(TaxonomicRank.FAMILY.name)

    @property
    def genus_name(self):
        return self.get_taxon_rank_name(TaxonomicRank.GENUS.name)

    @property
    def species_name(self):
        return self.get_taxon_rank_name(TaxonomicRank.SPECIES.name)

    @property
    def sub_species_name(self):
        return self.get_taxon_rank_name(TaxonomicRank.SUBSPECIES.name)

    @property
    def variety_name(self):
        self.get_taxon_rank_name(TaxonomicRank.VARIETY.name)

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

    def send_new_taxon_email(self, taxon_group_id=None):
        from bims.models import TaxonGroup

        current_site = Site.objects.get_current()
        recipients = get_recipients_for_notification(NEW_TAXONOMY)
        taxon_group = TaxonGroup.objects.get(id=taxon_group_id)
        email_body = render_to_string(
            'notifications/taxonomy/added_message.txt',
            {
                'taxonomy': self,
                'current_site': current_site,
                'taxon_group': taxon_group
            }
        )
        msg = EmailMultiAlternatives(
            '[{}] New Taxonomy email notification'.format(current_site),
            email_body,
            settings.DEFAULT_FROM_EMAIL,
            recipients
        )
        msg.send()


@receiver(models.signals.pre_save, sender=Taxonomy)
def taxonomy_pre_save_handler(sender, instance, **kwargs):
    """Get iucn status before save."""
    if instance.is_species and not instance.iucn_status:
        iucn_status = get_iucn_status(
            species_name=instance.canonical_name,
            only_returns_json=True
        )
        if iucn_status and 'result' in iucn_status:
            if len(iucn_status['result']) > 0:
                try:
                    iucn, _ = IUCNStatus.objects.get_or_create(
                        category=iucn_status['result'][0]['category']
                    )
                except IUCNStatus.MultipleObjectsReturned:
                    iucn = IUCNStatus.objects.filter(
                        category=iucn_status['result'][0]['category']
                    ).first()
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
    source = models.CharField(
        max_length=256,
        blank=True,
        default=''
    )
    uploader = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text='User who uploaded the taxon image (Optional)',
        related_name='taxon_image_uploader'
    )
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text='Owner of the taxon image (Optional)',
        related_name='taxon_image_owner'
    )
    date = models.DateField(
        null=True,
        blank=True
    )
    survey = models.ForeignKey(
        'bims.Survey',
        null=True,
        blank=True,
        on_delete=models.CASCADE
    )


def check_taxa_duplicates(taxon_name, taxon_rank):
    """
    Check for taxa duplicates, then merge if found
    :param taxon_name: Name of the taxon to check
    :param taxon_rank: Rank of the taxon to check
    :return: Merged taxonomy
    """
    from django.db.models import Q, Min
    from bims.utils.gbif import get_species
    from bims.utils.fetch_gbif import merge_taxa_data

    taxon_rank = taxon_rank.strip().upper()
    taxon_name = taxon_name.strip()
    taxa = Taxonomy.objects.filter(
        Q(canonical_name__iexact=taxon_name) |
        Q(legacy_canonical_name__icontains=taxon_name),
        rank=taxon_rank
    )
    if not taxa.count() > 1:
        return
    preferred_taxa = taxa
    accepted_taxa = taxa.filter(taxonomic_status='ACCEPTED')
    if accepted_taxa.exists():
        preferred_taxa = accepted_taxa
    preferred_taxon = preferred_taxa.values('gbif_key', 'id').annotate(
        Min('gbif_key')).order_by('gbif_key')[0]
    preferred_taxon_gbif_data = get_species(preferred_taxon['gbif_key'])
    preferred_taxon = Taxonomy.objects.get(
        id=preferred_taxon['id']
    )
    for taxon in taxa[1:]:
        gbif_data = get_species(taxon.gbif_key)
        if not preferred_taxon_gbif_data:
            preferred_taxon = taxon
            preferred_taxon_gbif_data = gbif_data
            continue
        if not gbif_data:
            continue
        if gbif_data['taxonomicStatus'] == 'ACCEPTED':
            preferred_taxon_gbif_data = gbif_data
            preferred_taxon = taxon
            continue
        if 'issues' in gbif_data and len(gbif_data['issues']) > 0:
            continue
        if 'nubKey' not in gbif_data:
            continue
        if (
            'taxonomicStatus' in gbif_data and
            gbif_data['taxonomicStatus'] != 'ACCEPTED'
        ):
            continue
        if 'key' not in preferred_taxon_gbif_data:
            preferred_taxon = taxon
            preferred_taxon_gbif_data = gbif_data
            continue
        if (
            'key' in gbif_data and
            gbif_data['key'] > preferred_taxon_gbif_data['key']
        ):
            continue
        preferred_taxon = taxon
        preferred_taxon_gbif_data = gbif_data

    merge_taxa_data(
        taxa_list=taxa.exclude(id=preferred_taxon.id),
        excluded_taxon=preferred_taxon
    )
    return preferred_taxon
