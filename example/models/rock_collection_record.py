# coding=utf-8
"""Rock collection record model definition.

"""

from django.db import models

from bims.models.biological_collection_record import \
    BiologicalCollectionRecord


class RockCollectionRecord(BiologicalCollectionRecord):
    """First collection model."""
    rock_name = models.CharField(
        max_length=50,
    )

    # noinspection PyClassicStyleClass
    class Meta:
        """Meta class for project."""
        app_label = 'example'
        verbose_name = 'rock'
        verbose_name_plural = 'rocks'
