# coding=utf-8
"""Biological collection record model definition.

"""
import json
import uuid
from django.conf import settings
from django.db import models
from django.dispatch import receiver
from django.utils import timezone
from django.contrib.postgres.fields import JSONField

from preferences import preferences
from bims.models.location_site import LocationSite
from bims.utils.gbif import update_collection_record
from bims.models.validation import AbstractValidation
from bims.models.taxonomy import Taxonomy
from bims.models.taxon_group import TaxonGroup
from bims.models.source_reference import SourceReference
from bims.enums.taxonomic_group_category import TaxonomicGroupCategory
from bims.models.bims_document import BimsDocument
from bims.models.survey import Survey
from td_biblio.models import Entry


class BiologicalCollectionQuerySet(models.QuerySet):
    def source_references(self):
        source_references = []
        unique_source_references = []
        is_doc = False
        for col in self:
            try:
                title = col.source_reference.title
                authors = col.source_reference.authors
                pub_year = col.source_reference.year
            except AttributeError:
                title = '-'
                authors = '-'
                pub_year = '-'

            if col.source_reference.is_published_report():
                if col.source_reference.source.doc_file:
                    url = col.source_reference.source.doc_file.url
                    is_doc = True
                else:
                    url = col.source_reference.source.doc_url
                bims_document, _ = BimsDocument.objects.get_or_create(
                    document=col.source_reference.source
                )
                try:
                    source = json.loads(
                        col.source_reference.source.supplemental_information
                    )['document_source']
                except:  # noqa
                    source = '-'
            else:
                try:
                    url = col.source_reference.source.doi
                    if not url:
                        url = col.source_reference.source.url
                except AttributeError:
                    if hasattr(col.source_reference, 'document'):
                        if col.source_reference.document:
                            if col.source_reference.document.doc_file:
                                url = (
                                    col.source_reference.document.doc_file.url
                                )
                                is_doc = True
                            else:
                                url = col.source_reference.document.doc_url
                        else:
                            url = '-'
                    else:
                        url = '-'

                try:
                    if col.source_reference.source_name:
                        source = col.source_reference.source_name
                    else:
                        source = (
                            col.source_reference.source.journal.name
                        )
                except AttributeError:
                    if isinstance(col.source_reference.source, Entry):
                        source = '-'
                    else:
                        source = col.source_reference.__str__()

            note = (
                col.source_reference.note if col.source_reference.note else '-'
            )

            if note is None:
                note = '-'

            item = {
                'Reference Category': col.source_reference.reference_type,
                'Author/s': authors,
                'Year': pub_year,
                'Title': title,
                'Source': source,
                'DOI/URL': url,
                'is_doc': is_doc,
                'Notes': note
            }
            if json.dumps(item) not in unique_source_references:
                source_references.append(item)
                unique_source_references.append(json.dumps(item))
        return sorted(
            source_references, key = lambda i: (
                i['Reference Category'], i['Author/s']))


class BiologicalCollectionManager(models.Manager):
    def get_queryset(self):
        return BiologicalCollectionQuerySet(self.model, using=self._db)

    def source_references(self):
        return self.get_queryset().source_references()


ABUNDANCE_TYPE_NUMBER = 'number'
ABUNDANCE_TYPE_PERCENTAGE = 'percentage'
ABUNDANCE_TYPE_DENSITY = 'density'
ABUNDANCE_TYPE_SPECIES_VALVE = 'species_valve_per_frustule_count'
ABUNDANCE_TYPE_DENSITY_CELLS_M2 = 'density_cells_per_m2'
ABUNDANCE_TYPE_DENSITY_CELLS_ML = 'density_cells_per_mL'


class BiologicalCollectionRecord(AbstractValidation):
    """Biological collection model."""
    CATEGORY_CHOICES = (
        ('alien', 'Non-Native'),
        ('indigenous', 'Native'),
    )

    HABITAT_CHOICES = (
        ('euryhaline', 'Euryhaline'),
        ('freshwater', 'Freshwater'),
    )

    ABUNDANCE_TYPE_CHOICES = (
        (ABUNDANCE_TYPE_NUMBER, 'Number'),
        (ABUNDANCE_TYPE_PERCENTAGE, 'Percentage'),
        (ABUNDANCE_TYPE_DENSITY, 'Density'),
        (ABUNDANCE_TYPE_SPECIES_VALVE, 'Species valve/frustule count'),
        (ABUNDANCE_TYPE_DENSITY_CELLS_M2, 'Density (cells/m2)'),
        (ABUNDANCE_TYPE_DENSITY_CELLS_ML, 'Density (cells/mL)'),
    )

    site = models.ForeignKey(
        LocationSite,
        models.CASCADE,
        related_name='biological_collection_record',
    )
    original_species_name = models.CharField(
        max_length=200,
        blank=True,
        default='',
    )
    present = models.BooleanField(
        default=True,
    )
    collection_date = models.DateField(
        default=timezone.now
    )
    collector = models.CharField(
        max_length=300,
        blank=True,
        default='',
        help_text='Collector name in string value, this is useful for '
                  'collector values from GBIF and other third party sources',
        verbose_name='collector or observer',
    )
    notes = models.TextField(
        blank=True,
        default='',
    )

    taxonomy = models.ForeignKey(
        Taxonomy,
        models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Taxonomy'
    )

    collection_habitat = models.CharField(
        max_length=200,
        choices=HABITAT_CHOICES,
        blank=True,
        default=''
    )

    institution_id = models.CharField(
        default=settings.INSTITUTION_ID_DEFAULT,
        help_text='An identifier for the institution having custody of the '
                  'object(s) or information referred to in the record.',
        max_length=200,
        verbose_name='Custodian',
    )

    sampling_method_string = models.CharField(
        max_length=50,
        blank=True,
        default=''
    )

    sampling_method = models.ForeignKey(
        'bims.SamplingMethod',
        null=True,
        blank=True,
        on_delete=models.SET_NULL
    )

    sampling_effort = models.CharField(
        max_length=50,
        blank=True,
        default=''
    )

    reference = models.CharField(
        max_length=300,
        blank=True,
        default=''
    )

    reference_category = models.CharField(
        max_length=200,
        blank=True,
        default=''
    )

    source_collection = models.CharField(
        help_text='e.g. SANBI',
        max_length=200,
        blank=True,
        default=''
    )

    upstream_id = models.CharField(
        help_text='Upstream id, e.g. Gbif key',
        max_length=200,
        blank=True,
        default=''
    )

    uuid = models.CharField(
        help_text='Collection record uuid',
        max_length=200,
        null=True,
        blank=True
    )

    additional_data = JSONField(
        blank=True,
        null=True
    )

    abundance_number = models.FloatField(
        blank=True,
        null=True
    )

    abundance_type = models.CharField(
        max_length=50,
        choices=ABUNDANCE_TYPE_CHOICES,
        default=ABUNDANCE_TYPE_NUMBER,
        blank=True
    )

    biotope = models.ForeignKey(
        'bims.Biotope',
        null=True,
        blank=True,
        on_delete=models.SET_NULL
    )

    specific_biotope = models.ForeignKey(
        'bims.Biotope',
        null=True,
        blank=True,
        related_name='specific_biotope',
        on_delete=models.SET_NULL
    )

    substratum = models.ForeignKey(
        'bims.Biotope',
        null=True,
        blank=True,
        related_name='biotope_substratum',
        on_delete=models.SET_NULL
    )

    source_reference = models.ForeignKey(
        SourceReference,
        null=True,
        blank=True,
        on_delete=models.SET_NULL
    )

    module_group = models.ForeignKey(
        'bims.TaxonGroup',
        help_text='Which module this collection belong to',
        null=True,
        blank=True,
        on_delete=models.SET_NULL
    )

    objects = BiologicalCollectionManager()

    survey = models.ForeignKey(
        'bims.Survey',
        related_name='biological_collection_record',
        null=True,
        on_delete=models.SET_NULL
    )

    @property
    def data_name(self):
        return self.original_species_name

    # noinspection PyClassicStyleClass
    class Meta:
        """Meta class for project."""
        app_label = 'bims'
        permissions = (
            ('can_upload_csv', 'Can upload CSV'),
            ('can_upload_shapefile', 'Can upload Shapefile'),
            ('can_validate_data', 'Can validate data'),
            ('can_add_single_occurrence', 'Can add single Occurrence'),
        )

    def on_post_save(self):
        if not self.taxonomy:
            update_collection_record(self)
        if not self.source_collection:
            if preferences.SiteSetting.default_data_source:
                self.source_collection = (
                    preferences.SiteSetting.default_data_source
                )
                self.save()
        if self.taxonomy and not self.module_group:
            # Get taxon group if exists
            taxonomies = [self.taxonomy.id]
            taxon_groups = TaxonGroup.objects.filter(
                taxonomies__in=taxonomies,
                category=TaxonomicGroupCategory.SPECIES_MODULE.name,
            )
            if taxon_groups.exists():
                self.module_group = taxon_groups[0]
                self.save()

    def save(self, *args, **kwargs):
        max_allowed = 10
        attempt = 0
        is_dictionary = False

        while not is_dictionary and attempt < max_allowed:
            if not self.additional_data:
                break
            if isinstance(self.additional_data, dict):
                is_dictionary = True
            else:
                self.additional_data = json.loads(self.additional_data)
                attempt += 1

        if not self.uuid:
            collection_uuid = str(uuid.uuid4())
            while BiologicalCollectionRecord.objects.filter(
                uuid=collection_uuid
            ).exists():
                collection_uuid = str(uuid.uuid4())
            self.uuid = collection_uuid

        if not self.original_species_name:
            self.original_species_name = self.taxonomy.canonical_name

        if not self.survey:
            try:
                survey, _ = Survey.objects.get_or_create(
                    site=self.site,
                    date=self.collection_date,
                    collector_user=self.collector_user,
                    owner=self.owner
                )
            except Survey.MultipleObjectsReturned:
                survey = Survey.objects.filter(
                    site=self.site,
                    date=self.collection_date,
                    collector_user=self.collector_user,
                    owner=self.owner
                )[0]
            self.survey = survey
        if (
            'gbif' in self.source_collection.lower()
            and not self.survey.validated
        ):
            self.survey.validated = True
            self.survey.save()

        if not self.survey.owner and self.owner:
            self.survey.owner = self.owner
            self.survey.save()

        super(BiologicalCollectionRecord, self).save(*args, **kwargs)

    def get_children(self):
        rel_objs = [f for f in self._meta.get_fields(include_parents=False)
                    if (f.one_to_many or f.one_to_one) and
                    f.auto_created and not f.concrete]

        for rel_obj in rel_objs:
            try:
                return getattr(self, rel_obj.get_accessor_name())
            except AttributeError:
                continue

    @staticmethod
    def get_children_model():
        rel_objs = [f for f in BiologicalCollectionRecord._meta.get_fields(
            include_parents=False)
                    if f.one_to_one and
                    f.auto_created and not f.concrete]
        related_models = []
        for rel_obj in rel_objs:
            related_models.append(rel_obj.related_model)
        return related_models

    def __init__(self, *args, **kwargs):
        super(BiologicalCollectionRecord, self).__init__(*args, **kwargs)
        self.__original_validated = self.validated

    def is_cluster_generation_applied(self):
        if self.__original_validated != self.validated:
            return True
        if self.validated:
            return True
        return False

    def __unicode__(self):
        label = '{species} - {date}'.format(
            species=self.original_species_name,
            date=self.collection_date
        )
        return label

    def __str__(self):
        label = '{species} - {date}'.format(
            species=self.original_species_name,
            date=self.collection_date
        )
        return label


@receiver(models.signals.post_save)
def collection_post_save_handler(sender, instance, **kwargs):
    """
    Fetch taxon from original species name.
    """

    if not issubclass(sender, BiologicalCollectionRecord):
        return
    models.signals.post_save.disconnect(
        collection_post_save_handler,
    )
    instance.on_post_save()
    models.signals.post_save.connect(
        collection_post_save_handler,
    )


@receiver(models.signals.post_save)
def collection_post_save_update_cluster(sender, instance, **kwargs):
    if not issubclass(sender, BiologicalCollectionRecord):
        return


@receiver(models.signals.post_delete)
def cluster_post_delete_handler(sender, instance, using, **kwargs):
    if not issubclass(sender, BiologicalCollectionRecord) and \
            not issubclass(sender, LocationSite):
        return
