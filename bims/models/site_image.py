# coding=utf-8
"""
    Site Image model definition.
    To store images for location site.
"""
from django.utils import timezone

from django.db import models
from sass.models.site_visit import SiteVisit
from bims.models.survey import Survey

COLLECTION_RECORD_KEY = 'collection_record'
SITE_KEY = 'site'
WATER_TEMPERATURE_KEY = 'water_temperature'


FORM_CHOICES = (
    (COLLECTION_RECORD_KEY, 'Collection Record'),
    (SITE_KEY, 'Site'),
    (WATER_TEMPERATURE_KEY, 'Water Temperature'),
)


class SiteImage(models.Model):

    form_uploader = models.CharField(
        max_length=100,
        default='',
        blank=True,
        choices=FORM_CHOICES
    )

    notes = models.TextField(
        default='',
        null=True,
        blank=True
    )

    site = models.ForeignKey(
        'bims.LocationSite',
        null=False,
        blank=False,
        on_delete=models.CASCADE
    )

    image = models.ImageField(
        upload_to='site_images',
        null=False,
        blank=False
    )

    site_visit = models.ForeignKey(
        SiteVisit,
        null=True,
        blank=True,
        on_delete=models.SET_NULL
    )

    survey = models.ForeignKey(
        Survey,
        null=True,
        blank=True,
        on_delete=models.SET_NULL
    )

    date = models.DateField(
        null=False,
        blank=False,
        default=timezone.now
    )

    @property
    def image_date(self):
        if self.survey:
            return self.survey.date
        if self.site_visit:
            return self.site_visit.site_visit_date
        return self.date
