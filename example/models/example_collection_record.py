# coding=utf-8
"""Example collection record model definition.

"""

from django.db import models

from bims.models.biological_collection_record import \
    BiologicalCollectionRecord


class ExampleCollectionRecord(BiologicalCollectionRecord):
    """First collection model."""
    HABITAT_CHOICES = (
        ('euryhaline', 'Euryhaline'),
        ('freshwater', 'Freshwater'),
    )

    habitat = models.CharField(
        max_length=50,
        choices=HABITAT_CHOICES,
        blank=True,
    )

    # noinspection PyClassicStyleClass
    class Meta:
        """Meta class for project."""
        app_label = 'example'
        verbose_name = 'fish'
        verbose_name_plural = 'fishes'
