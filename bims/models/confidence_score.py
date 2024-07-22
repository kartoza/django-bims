from django.db import models


class DataConfidenceScore(models.Model):
    """Model to store confidence scores for data"""

    reliability_of_sources = models.IntegerField(
        default=0,
        help_text='Score for the reliability of the sources (0-100).'
    )
    certainty_of_identification = models.CharField(
        default='',
        blank=True,
    )
    accuracy_of_coordinates = models.CharField(
        default='',
        blank=True
    )

    class Meta:
        abstract = True
