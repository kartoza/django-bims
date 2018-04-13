# coding=utf-8
"""Taxon model definition.

"""

from django.db import models
from django.dispatch import receiver
from bims.models.iucn_status import IUCNStatus
from bims.utils.iucn import get_iucn_status


class Taxon(models.Model):
    """Taxon model."""

    gbif_id = models.IntegerField(
        verbose_name='GBIF id',
        null=True,
        blank=True,
    )
    iucn_status = models.ForeignKey(
        IUCNStatus,
        models.SET_NULL,
        null=True,
        blank=True,
    )
    common_name = models.CharField(
        max_length=100,
        blank=True,
        default='',
    )
    scientific_name = models.CharField(
        max_length=100,
        blank=True,
        default='',
    )
    author = models.CharField(
        max_length=100,
        blank=True,
        default='',
    )

    # noinspection PyClassicStyleClass
    class Meta:
        """Meta class for project."""
        app_label = 'bims'
        verbose_name_plural = 'Taxa'
        verbose_name = 'Taxon'

    def __str__(self):
        return "%s (%s)" % (self.common_name, self.iucn_status)


@receiver(models.signals.pre_save, sender=Taxon)
def taxon_pre_save_handler(sender, instance, **kwargs):
    """Get iucn status before save."""
    if instance.common_name and not instance.iucn_status:
        iucn_status = get_iucn_status(
            species_name=instance.common_name
        )
        if iucn_status:
            instance.iucn_status = iucn_status
