# coding=utf-8
"""Survey model definition.

"""

from django.db import models
from django.utils import timezone
from django.dispatch import receiver
from bims.models import LocationSite
from bims.models.validation import AbstractValidation


class Survey(AbstractValidation):
    """Survey model, this behaves like a site_visit but for general use."""
    site = models.ForeignKey(
        LocationSite,
        models.CASCADE,
        null=True,
        related_name='survey',
    )

    date = models.DateField(
        default=timezone.now
    )

    collector_string = models.CharField(
        max_length=500,
        blank=True,
        default='',
        help_text='Collector name in string value, this is useful for '
                  'collector values from GBIF and other third party sources',
        verbose_name='collector or observer',
    )

    @property
    def sass_site_visit(self):
        try:
            return (
                self.biological_collection_record
                    .first()
                    .sitevisittaxon
                    .site_visit
            )
        except AttributeError:
            return None

    @property
    def data_name(self):
        if not self.site:
            return self.id
        site = (
            self.site.name if not self.site.site_code else
            self.site.site_code)
        return site

    def __unicode__(self):
        return '{date} - {survey}'.format(
            date=self.date,
            survey=self.data_name
        )

    def __str__(self):
        return '{date} - {survey}'.format(
            date=self.date,
            survey=self.data_name
        )

    class Meta:
        ordering = ('-date',)


class SurveyData(models.Model):
    """Survey data model."""
    name = models.CharField(
        max_length=200,
        blank=False,
        null=False,
    )
    display_order = models.IntegerField(default=0)

    def __unicode__(self):
        return self.name


class SurveyDataOption(models.Model):
    """Survey data option model."""
    survey_data = models.ForeignKey(
        SurveyData,
        on_delete=models.CASCADE
    )
    option = models.CharField(
        max_length=200,
        blank=False,
        null=False
    )
    display_order = models.IntegerField(default=0)

    def __unicode__(self):
        return '{data} - {option}'.format(
            data=self.survey_data.name,
            option=self.option
        )


class SurveyDataValue(models.Model):
    """Survey data value model."""
    survey = models.ForeignKey(
        Survey,
        on_delete=models.CASCADE)

    survey_data = models.ForeignKey(
        SurveyData,
        on_delete=models.CASCADE
    )

    survey_data_option = models.ForeignKey(
        SurveyDataOption,
        on_delete=models.CASCADE
    )
