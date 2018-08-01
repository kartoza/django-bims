# coding=utf-8
"""Biological collection record model definition.

"""

from django.conf import settings
from django.db import models
from django.dispatch import receiver
from django.utils import timezone

from bims.models.location_site import LocationSite
from bims.models.taxon import Taxon
from bims.utils.cluster import (
    update_cluster_by_collection,
    update_cluster_by_site
)
from bims.utils.gbif import update_collection_record


class BiologicalCollectionRecord(models.Model):
    """Biological collection model."""
    CATEGORY_CHOICES = (
        ('alien', 'Alien'),
        ('indigenous', 'Indigenous'),
        ('translocated', 'Translocated')
    )
    site = models.ForeignKey(
        LocationSite,
        models.CASCADE,
        related_name='biological_collection_record',
    )
    original_species_name = models.CharField(
        max_length=100,
        blank=True,
        default='',
    )
    category = models.CharField(
        max_length=50,
        choices=CATEGORY_CHOICES,
        blank=True,
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
        max_length=100,
        blank=True,
        default='',
        verbose_name='collector or observer',
    )
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        models.SET_NULL,
        blank=True,
        null=True,
    )
    notes = models.TextField(
        blank=True,
        default='',
    )
    taxon_gbif_id = models.ForeignKey(
        Taxon,
        models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Taxon GBIF ',
    )
    validated = models.BooleanField(
        default=False,
    )

    # noinspection PyClassicStyleClass
    class Meta:
        """Meta class for project."""
        app_label = 'bims'
        permissions = (
            ('can_upload_csv', 'Can upload CSV'),
            ('can_upload_shapefile', 'Can upload Shapefile'),
            ('can_validate_data', 'Can validate data'),
        )

    def on_post_save(self):
        if not self.taxon_gbif_id:
            update_collection_record(self)

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
                    if (f.one_to_many or f.one_to_one) and
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
    if instance.is_cluster_generation_applied():
        update_cluster_by_collection(instance)
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
    if issubclass(sender, BiologicalCollectionRecord):
        if instance.is_cluster_generation_applied():
            update_cluster_by_collection(instance)
    if issubclass(sender, LocationSite):
        update_cluster_by_site(instance)
