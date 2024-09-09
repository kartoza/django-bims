import uuid
from django.db import models


class Dataset(models.Model):
    """Model to store dataset information"""

    uuid = models.UUIDField(
        default=uuid.uuid4,
        editable=True,
        unique=True,
    )
    name = models.CharField(
        max_length=255,
        help_text='Name of the dataset'
    )
    abbreviation = models.CharField(
        max_length=50,
        blank=True,
        help_text='Abbreviation of the dataset (e.g., iNat for iNaturalist)'
    )
    description = models.TextField(
        blank=True,
        help_text='Description of the dataset'
    )
    citation = models.TextField(
        blank=True,
        help_text='Citation of the dataset'
    )
    url = models.CharField(
        blank=True,
        help_text='URL of the dataset'
    )

    class Meta:
        verbose_name = 'Dataset'
        verbose_name_plural = 'Datasets'
        ordering = ['name']

    def __str__(self):
        return self.name
