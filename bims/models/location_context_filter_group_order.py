from django.contrib.gis.db import models
from django.dispatch import receiver
from django.db.models.signals import post_save


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

    @property
    def filter_display_order(self):
        return self.filter.display_order

    class Meta:
        ordering = ['filter__display_order', 'group_display_order']


@receiver(post_save, sender=LocationContextFilterGroupOrder)
def site_visit_post_save_handler(**kwargs):
    from bims.tasks.location_context import generate_spatial_scale_filter
    import os
    from django.conf import settings
    file_name = 'spatial_scale_filter_list.txt'
    file_path = os.path.join(
        settings.MEDIA_ROOT,
        file_name
    )
    generate_spatial_scale_filter.delay(file_path)
