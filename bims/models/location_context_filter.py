from django.contrib.gis.db import models


class LocationContextFilter(models.Model):
    title = models.CharField(
        max_length=200,
        null=False,
        blank=False
    )
    display_order = models.IntegerField(
        null=False,
        blank=False
    )
    location_context_groups = models.ManyToManyField(
        'bims.LocationContextGroup',
        through='bims.LocationContextFilterGroupOrder'
    )

    def __str__(self):
        return self.title
