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

from bims.models.location_site import LocationSite
from bims.utils.gbif import update_collection_record
from bims.models.validation import AbstractValidation
from bims.models.document_links_mixin import DocumentLinksMixin
from bims.models.taxonomy import Taxonomy


class BiologicalCollectionRecord(
    AbstractValidation, DocumentLinksMixin):
    """Biological collection model."""
    CATEGORY_CHOICES = (
        ('alien', 'Non-Native'),
        ('indigenous', 'Native'),
    )

    HABITAT_CHOICES = (
        ('euryhaline', 'Euryhaline'),
        ('freshwater', 'Freshwater'),
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
    category = models.CharField(
        max_length=50,
        choices=CATEGORY_CHOICES,
        blank=True,
        null=True,
    )
    present = models.BooleanField(
        default=True,
    )
    absent = models.BooleanField(
        default=True,
    )
    collection_date = models.DateField(
        default=timezone.now
    )
    collector = models.CharField(
        max_length=300,
        blank=True,
        default='',
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
        null=True,
    )

    upstream_id = models.CharField(
        help_text='Upstream id, e.g. Gbif key',
        max_length=200,
        blank=True,
        null=True
    )

    uuid = models.UUIDField(
        help_text='Collection record uuid',
        max_length=200,
        null=True,
        blank=True
    )

    additional_data = JSONField(
        blank=True,
        null=True
    )

    abundance_number = models.IntegerField(
        blank=True,
        null=True
    )

    biotope = models.ForeignKey(
        'bims.Biotope',
        null=True,
        blank=True,
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
            collection_uuid = uuid.uuid4()
            while BiologicalCollectionRecord.objects.filter(
                uuid=collection_uuid
            ).exists():
                collection_uuid = uuid.uuid4()
            self.uuid = collection_uuid

        # Try to get category if empty
        if not self.category:
            bio_with_category = BiologicalCollectionRecord.objects.filter(
                taxonomy__canonical_name__icontains=
                self.taxonomy.canonical_name,
                category__isnull=False
            )
            if bio_with_category.exists():
                self.category = bio_with_category[0].category

        if not self.original_species_name:
            self.original_species_name = self.taxonomy.canonical_name

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
        label = '{species} - {collector} - {date}'.format(
            species=self.original_species_name,
            collector=self.collector,
            date=self.collection_date
        )
        return label


@receiver(models.signals.post_save)
def collection_post_save_handler(sender, instance, **kwargs):
    """
    Fetch taxon from original species name.
    """
    from bims.models import SearchProcess

    if not issubclass(sender, BiologicalCollectionRecord):
        return
    models.signals.post_save.disconnect(
        collection_post_save_handler,
    )
    instance.on_post_save()
    if instance.is_cluster_generation_applied():
        SearchProcess.objects.all().delete()
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
