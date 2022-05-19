import json
from django.utils import timezone
from django.contrib.gis.db import models
from django.db.models import Q
from django.contrib.postgres.fields import JSONField
from bims.models import LocationSite, SourceReference, Survey
from bims.models.biological_collection_record import (
    BiologicalCollectionQuerySet
)


class ChemicalRecordManager(models.Manager):
    def get_queryset(self):
        return BiologicalCollectionQuerySet(self.model, using=self._db)

    def source_references(self):
        return self.get_queryset().source_references()


class ChemicalRecord(models.Model):

    objects = ChemicalRecordManager()

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
                    date=self.date
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


def physico_chemical_chart_data(
        location_site: LocationSite,
        chem_codes = None
    ) -> dict:
    """
    Returns serialized physico-chemical data for chart purpose
    :param location_site: Location Site object
    :param chem_codes: list of chemical codes to be displayed in the chart
    """
    from bims.serializers.chemical_records_serializer import (
        ChemicalRecordsSerializer
    )
    list_chems = {}
    if location_site:
        chems = ChemicalRecord.objects.filter(
            Q(location_site_id=location_site.id) |
            Q(survey__site_id=location_site.id)
        )
        if chem_codes is None:
            chem_codes = list(chems.values_list(
                'chem__chem_code', flat=True
            ).distinct())
        x_label = []
        for chem in chem_codes:
            chem_name = chem.lower().replace('-n', '').upper()
            qs = chems.filter(chem__chem_code=chem).order_by('date')
            if not qs.exists():
                continue
            value = ChemicalRecordsSerializer(qs, many=True)

            # Get chemical unit
            chem_unit = qs.first().chem.chem_unit.unit

            data = {
                'unit': chem_unit,
                'name': qs.first().chem.chem_description,
                'values': value.data
            }
            for val in value.data:
                if val['str_date'] not in x_label:
                    x_label.append(val['str_date'])
            try:
                list_chems[chem_name].append({chem: data})
            except KeyError:
                list_chems[chem_name] = [{chem: data}]
    return list_chems
