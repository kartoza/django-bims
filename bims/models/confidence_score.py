from django.db import models


class DataConfidenceScore(models.Model):
    """Model to store confidence scores for data"""

    accuracy_of_identification = models.IntegerField(
        default=0,
        help_text='Score for the accuracy of identification (0-100).'
    )
    accuracy_of_locality = models.IntegerField(
        default=0,
        help_text='Score for the accuracy of locality information (0-100).'
    )
    reliability_of_sources = models.IntegerField(
        default=0,
        help_text='Score for the reliability of the sources (0-100).'
    )

    class Meta:
        abstract = True
