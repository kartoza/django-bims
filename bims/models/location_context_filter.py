from django.contrib.gis.db import models
from django.contrib.sites.models import Site


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
    site = models.ForeignKey(
        Site,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name="Associated Site",
        help_text="The site this LocationContextFilter is associated with."
    )

    def __str__(self):
        return self.title
