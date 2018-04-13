# coding=utf-8
"""Survey model definition.

"""

from django.db import models
from django.utils import timezone
from bims.models import LocationSite


class Survey(models.Model):
    """Survey model."""

    date = models.DateField(
        default=timezone.now
    )

    sites = models.ManyToManyField(LocationSite)
