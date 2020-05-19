# coding=utf-8
"""Site visit model definition.
"""
from django.contrib.gis.db import models
from django.conf import settings
from django.utils import timezone
from django.dispatch import receiver
from django.db.models.signals import post_save

from bims.models import LocationSite
from bims.utils.logger import log
from sass.enums.water_level import (
    WaterLevel,
    WATER_LEVEL_NAME,
)
from sass.enums.channel_type import (
    ChannelType,
    CHANNEL_TYPE_NAME,
)
from sass.enums.water_turbidity import WaterTurbidity
from sass.enums.canopy_cover import CanopyCover
from sass.models.abstract_additional_data import AbstractAdditionalData

EMBEDDEDNESS_1 = '0-25'
EMBEDDEDNESS_2 = '26-50'
EMBEDDEDNESS_3 = '51-75'
EMBEDDEDNESS_4 = '76-100'


class SiteVisit(AbstractAdditionalData):
    """Site visit model."""
    EMBEDDEDNESS_CHOICES = (
        (EMBEDDEDNESS_1, '0-25'),
        (EMBEDDEDNESS_2, '26-50'),
        (EMBEDDEDNESS_3, '51-75'),
        (EMBEDDEDNESS_4, '76-100')
    )

    location_site = models.ForeignKey(
        LocationSite,
        on_delete=models.CASCADE,
        default=None
    )

    site_visit_date = models.DateField(
        default=timezone.now
    )

    time = models.DateTimeField(
        null=True,
        blank=True
    )

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        help_text='Creator/owner of this data from the web',
        null=True,
        blank=True,
        related_name='%(class)s_owner',
        on_delete=models.SET_NULL
    )

    collector = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        help_text='Actual capturer/collector of this data',
        null=True,
        blank=True,
        related_name='%(class)s_data_collector',
        on_delete=models.SET_NULL
    )

    water_level = models.CharField(
        max_length=100,
        choices=[
            (status.name, status.value[WATER_LEVEL_NAME])
            for status in WaterLevel],
        blank=True,
        null=True
    )

    channel_type = models.CharField(
        max_length=200,
        choices=[
            (status.name, status.value[CHANNEL_TYPE_NAME])
            for status in ChannelType],
        blank=True,
        null=True
    )

    water_turbidity = models.CharField(
        max_length=100,
        choices=[
            (status.name, status.value)
            for status in WaterTurbidity],
        blank=True,
        null=True
    )

    canopy_cover = models.CharField(
        max_length=100,
        choices=[
            (status.name, status.value)
            for status in CanopyCover],
        blank=True,
        null=True
    )

    embeddedness = models.CharField(
        max_length=50,
        choices=EMBEDDEDNESS_CHOICES,
        blank=True,
        default=''
    )

    average_velocity = models.IntegerField(
        null=True,
        blank=True
    )

    average_depth = models.IntegerField(
        null=True,
        blank=True
    )

    discharge = models.IntegerField(
        null=True,
        blank=True
    )

    sass_version = models.IntegerField(
        null=True,
        blank=True
    )

    sass_biotope_fraction = models.ManyToManyField(
        'sass.SassBiotopeFraction',
        blank=True
    )

    other_biota = models.TextField(
        null=True,
        blank=True
    )

    comments_or_observations = models.TextField(
        null=True,
        blank=True
    )

    data_source = models.ForeignKey(
        'bims.DataSource',
        null=True,
        blank=True,
        on_delete=models.SET_NULL
    )

    def __unicode__(self):
        return self.location_site.name


@receiver(post_save, sender=SiteVisit)
def site_visit_post_save_handler(**kwargs):
    from sass.scripts.site_visit_ecological_condition_generator import (
        generate_site_visit_ecological_condition
    )
    try:
        site_visit = kwargs['instance']
    except KeyError:
        return
    log('Generate site visit ecological condition')
    site_visits = list()
    site_visits.append(site_visit)
    generate_site_visit_ecological_condition(site_visits)
