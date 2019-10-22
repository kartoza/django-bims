import json
from django.contrib.gis.db import models
from django.contrib.postgres.fields import JSONField
from bims.models import LocationSite, SourceReference


class ChemicalRecord(models.Model):

    date = models.DateField(
        null=False,
        blank=False
    )

    value = models.FloatField(
        null=True,
        blank=True
    )

    location_site = models.ForeignKey(
        LocationSite,
        models.CASCADE,
        related_name='chemical_collection_record',
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

    def save(self, *args, **kwargs):
        max_allowed = 10
        attempt = 0
        is_dictionary = False

        while not is_dictionary and attempt < max_allowed:
            if not self.additional_data:
                break
            if isinstance(self.additional_data, dict):
                is_dictionary = True
            else:
                self.additional_data = json.loads(self.additional_data)
                attempt += 1

        super(ChemicalRecord, self).save(*args, **kwargs)
