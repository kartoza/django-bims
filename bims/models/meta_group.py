# coding=utf-8
"""MetaGroup model definition.

Broader organism group classification.  Sits above TaxonGroup in the hierarchy:

    Taxon → TaxonGroup (module) → MetaGroup
"""
from django.db import models


class MetaGroup(models.Model):
    """
    A broader organism group (metagroup) used to classify biodiversity modules.

    Examples: Macroinvertebrates
    """

    name = models.CharField(
        max_length=200,
        unique=True,
    )

    description = models.TextField(
        blank=True,
        help_text='Optional description of this metagroup.',
    )

    gbif_key = models.CharField(
        max_length=50,
        blank=True,
        help_text=(
            'Corresponding GBIF broader organism group key'
        ),
    )

    logo = models.ImageField(
        upload_to='metagroup_logo',
        null=True,
        blank=True,
        help_text='Representative icon or logo for this metagroup.',
    )

    display_order = models.IntegerField(
        null=True,
        blank=True,
        help_text='Controls the display order on the landing page widget.',
    )

    class Meta:
        ordering = ('display_order', 'name')
        verbose_name = 'Meta Group'
        verbose_name_plural = 'Meta Groups'

    def __str__(self):
        return self.name
