from django.contrib.gis.db import models
from django.utils import timezone


class LocationContextQuerySet(models.QuerySet):
    def value_from_key(self, key):
        values = self.filter(
            key=key
        ).values_list(
            'value', flat=True
        )
        if len(values) > 0:
            return values[0]
        else:
            return '-'

    def values_from_group(self, group):
        group_values = dict()
        values = self.filter(
            group_key=group
        )
        for value in values:
            group_values[value.key] = value.value
        return group_values


class LocationContextManager(models.Manager):
    def get_queryset(self):
        return LocationContextQuerySet(self.model, using=self._db)

    def value_from_key(self, key):
        return self.get_queryset().value_from_key(key)

    def values_from_group(self, group):
        return self.get_queryset().values_from_group(group)


class LocationContext(models.Model):
    site = models.ForeignKey(
        'bims.LocationSite',
        on_delete=models.CASCADE
    )
    key = models.CharField(
        max_length=100,
        blank=True,
        default=''
    )
    name = models.CharField(
        max_length=255,
        blank=True,
        default=''
    )
    value = models.CharField(
        max_length=255,
        blank=True,
        default=''
    )
    group_key = models.CharField(
        max_length=255,
        blank=True,
        default=''
    )
    fetch_time = models.DateTimeField(
        default=timezone.now
    )
    objects = LocationContextManager()
