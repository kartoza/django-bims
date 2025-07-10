from bims.utils.decorator import prevent_recursion
from django.contrib.gis.db import models
from django.dispatch.dispatcher import receiver
from django.utils import timezone
from django.db import ProgrammingError


class LocationContextQuerySet(models.QuerySet):
    def value_from_key(self, key='', layer_name=''):
        if layer_name:
            from cloud_native_gis.models import Layer
            layer = Layer.objects.filter(name__istartswith=layer_name).first()
            if layer:
                key = layer.unique_id
        try:
            values = self.filter(
                group__key=key
            ).order_by(
                '-fetch_time'
            ).values_list(
                'value', flat=True
            )
        except ProgrammingError:
            values = self.filter(
                group__key=key
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
            group__geocontext_group_key=group
        )
        for value in values:
            group_values[value.group.key] = value.value
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
    value = models.CharField(
        max_length=255,
        blank=True,
        default=''
    )
    group = models.ForeignKey(
        'bims.LocationContextGroup',
        null=True,
        blank=True,
        on_delete=models.CASCADE
    )
    fetch_time = models.DateTimeField(
        default=timezone.now
    )
    objects = LocationContextManager()

    class Meta:
      indexes = [
        models.Index(fields=['group', 'value']),
      ]


@receiver(models.signals.post_save, sender=LocationContext)
@prevent_recursion
def location_context_post_save(sender, instance, **kwargs):
    """
    Post save location context
    """
    if ',' in instance.value:
        instance.value = instance.value.replace(',', '')
