import json
from django.utils import timezone
from django.contrib.gis.db import models
from django.contrib.postgres.fields import JSONField
from bims.models import LocationSite, SourceReference, Survey


class ChemicalRecord(models.Model):

    date = models.DateField(
        null=False,
        blank=False,
        default=timezone.now
    )

    value = models.FloatField(
        null=True,
        blank=True
    )

    location_site = models.ForeignKey(
        LocationSite,
        models.CASCADE,
        null=True,
        related_name='chemical_collection_record',
        blank=True
    )

    survey = models.ForeignKey(
        'bims.Survey',
        models.CASCADE,
        related_name='chemical_collection_record',
        null=True,
        blank=True
    )

    chem = models.ForeignKey(
        'bims.Chem',
        models.CASCADE,
        related_name='chemical_collection_record',
        null=True,
        blank=True
    )

    additional_data = JSONField(
        null=True,
        blank=True
    )

    source_reference = models.ForeignKey(
        SourceReference,
        null=True,
        blank=True,
        on_delete=models.SET_NULL
    )

    def __str__(self):
        site = self.location_site
        if not site and self.survey:
            site = self.survey.site
        return '{site} - {value} - {date}'.format(
            site=site.location_site_identifier,
            value=self.value,
            date=self.date
        )

    def save(self, *args, **kwargs):
        max_allowed = 10
        attempt = 0
        is_dictionary = False

        if not self.survey and self.location_site:
            survey = Survey.objects.filter(
                site=self.location_site,
                date=self.date
            ).first()

            if not survey:
                survey = Survey.objects.create(
                    site=self.location_site,
                    data=self.date
                )
            self.survey = survey

        while not is_dictionary and attempt < max_allowed:
            if not self.additional_data:
                break
            if isinstance(self.additional_data, dict):
                is_dictionary = True
            else:
                self.additional_data = json.loads(self.additional_data)
                attempt += 1

        super(ChemicalRecord, self).save(*args, **kwargs)
