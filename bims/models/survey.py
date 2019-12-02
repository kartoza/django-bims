# coding=utf-8
"""Survey model definition.

"""

from django.db import models
from django.utils import timezone
from bims.models import LocationSite
from bims.models.validation import AbstractValidation


class Survey(AbstractValidation):
    """Survey model."""
    site = models.ForeignKey(
        LocationSite,
        models.CASCADE,
        null=True,
        related_name='survey',
    )

    date = models.DateField(
        default=timezone.now
    )

    @property
    def data_name(self):
        if not self.site:
            return self.id
        site = (
            self.site.name if not self.site.site_code else
            self.site.site_code)
        return site
