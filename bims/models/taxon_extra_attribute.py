# coding=utf-8
"""Taxon extra attribute model definition

"""

from django.db import models, transaction
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

from bims.models.taxon_group import TaxonGroup
from bims.tasks.taxon_extra_attribute import (
    add_taxa_attribute,
    remove_taxa_attribute
)


class TaxonExtraAttribute(models.Model):
    name = models.CharField(
        max_length=255,
        null=False,
        blank=False
    )

    taxon_group = models.ForeignKey(
        TaxonGroup,
        null=False,
        blank=False,
        on_delete=models.CASCADE
    )

    class Meta:
        ordering = ('name', )


@receiver(post_save, sender=TaxonExtraAttribute)
def taxon_extra_attribute_post_save(sender, instance, **kwargs):
    def on_commit():
        add_taxa_attribute.delay(instance.id)
    transaction.on_commit(on_commit)


@receiver(post_delete, sender=TaxonExtraAttribute)
def taxon_extra_attribute_post_delete(sender, instance, **kwargs):
    remove_taxa_attribute.delay(instance.id)
