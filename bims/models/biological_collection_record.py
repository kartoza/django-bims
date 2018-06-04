# coding=utf-8
"""Biological collection record model definition.

"""

from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone
from django.dispatch import receiver

from bims.models.location_site import LocationSite
from bims.utils.gbif import update_fish_collection_record
from bims.utils.cluster import update_cluster
from bims.models.taxon import Taxon


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
    )
    owner = models.ForeignKey(
        User,
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

    def on_post_save(self):
        update_fish_collection_record(self)

    def get_children(self):
        rel_objs = [f for f in self._meta.get_fields(include_parents=False)
                    if (f.one_to_many or f.one_to_one) and
                    f.auto_created and not f.concrete]

        for rel_obj in rel_objs:
            try:
                return getattr(self, rel_obj.get_accessor_name())
            except AttributeError:
                continue


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
    update_cluster(instance)
    models.signals.post_save.connect(
        collection_post_save_handler,
    )
