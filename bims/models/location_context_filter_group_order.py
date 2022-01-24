from django.contrib.gis.db import models
from django.dispatch import receiver
from django.db.models.signals import post_save
from bims.models.location_context_group import LocationContextGroup
from bims.models.location_context_filter import LocationContextFilter


class LocationContextFilterGroupOrder(models.Model):
    group = models.ForeignKey(
        'bims.LocationContextGroup',
        on_delete=models.CASCADE
    )
    filter = models.ForeignKey(
        'bims.LocationContextFilter',
        on_delete=models.CASCADE
    )
    group_display_order = models.IntegerField(
        null=False,
        blank=False
    )
    show_in_dashboard = models.BooleanField(
        default=False,
        help_text='Show this location context group in dashboard'
    )
    show_in_side_panel = models.BooleanField(
        default=False,
        help_text='Show this location context group in side panel'
    )

    @property
    def filter_display_order(self):
        return self.filter.display_order

    class Meta:
        ordering = ['filter__display_order', 'group_display_order']


@receiver(post_save, sender=LocationContextFilterGroupOrder)
@receiver(post_save, sender=LocationContextGroup)
@receiver(post_save, sender=LocationContextFilter)
def location_context_post_save_handler(**kwargs):
    from bims.tasks.location_context import generate_spatial_scale_filter
    generate_spatial_scale_filter.delay()
