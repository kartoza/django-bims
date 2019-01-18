# -*- coding: utf-8 -*-
from django.contrib.gis.db import models
from django.utils import timezone
from sass.enums.sass5_rating import SASS5Rating


class SASS5Sheet(models.Model):

    date = models.DateTimeField(
        default=timezone.now
    )

    rhp_site_code = models.CharField(
        verbose_name='RHP Site Code',
        help_text='RHP Site Code',
        max_length=10,
        null=True,
        blank=True
    )

    collector_sampler = models.CharField(
        verbose_name='Collector/Sampler',
        help_text='Collector/Sampler',
        max_length=255,
        null=True,
        blank=True
    )

    location_site = models.ForeignKey(
        'bims.LocationSite',
        null=True,
        blank=True
    )

    temp_centigrade = models.FloatField(
        verbose_name='Temp (˚C)',
        help_text='Temp (˚C)',
        null=True,
        blank=True
    )

    ph = models.FloatField(
        verbose_name='pH',
        help_text='pH',
        null=True,
        blank=True
    )

    do_mg_per_litre = models.FloatField(
        verbose_name='DO (mg/L)',
        help_text='DO (mg/L)',
        null=True,
        blank=True
    )

    flow = models.FloatField(
        verbose_name='Flow',
        help_text='Flow',
        null=True,
        blank=True
    )

    riparian_disturbance = models.CharField(
        verbose_name='Riparian Disturbance',
        help_text='Riparian Disturbance',
        max_length=100,
        null=True,
        blank=True
    )

    instream_disturbance = models.CharField(
        verbose_name='Instream Disturbance',
        help_text='Instream Disturbance',
        max_length=100,
        null=True,
        blank=True
    )

    zonation = models.CharField(
        verbose_name='Zonation',
        help_text='Zonation',
        max_length=100,
        null=True,
        blank=True
    )

    biotope_stones_in_current = models.CharField(
        verbose_name='Biotope Stones In Current (SIC)',
        help_text='Biotope Stones In Current (SIC)',
        max_length=10,
        null=True,
        blank=True,
        choices=[(rating.name, rating.value) for rating in SASS5Rating]
    )

    biotope_stones_out_of_current = models.CharField(
        verbose_name='Biotope Stones Out Of Current (SOOC)',
        help_text='Biotope Stones Out Of Current (SOOC)',
        max_length=10,
        null=True,
        blank=True,
        choices=[(rating.name, rating.value) for rating in SASS5Rating]
    )

    biotope_bedrock = models.CharField(
        verbose_name='Biotope Bedrock',
        help_text='Biotope Bedrock',
        max_length=10,
        null=True,
        blank=True,
        choices=[(rating.name, rating.value) for rating in SASS5Rating]
    )

    biotope_aquatic_vegetation = models.CharField(
        verbose_name='Biotope Aquatic Veg',
        help_text='Biotope Aquatic Veg',
        max_length=10,
        null=True,
        blank=True,
        choices=[(rating.name, rating.value) for rating in SASS5Rating]
    )

    biotope_margin_veg_in_current = models.CharField(
        verbose_name='Biotope MargVeg In Current',
        help_text='Biotope MargVeg In Current',
        max_length=10,
        null=True,
        blank=True,
        choices=[(rating.name, rating.value) for rating in SASS5Rating]
    )

    biotope_margin_veg_out_of_current = models.CharField(
        verbose_name='Biotope MargVeg Out Of Current',
        help_text='Biotope MargVeg Out Of Current',
        max_length=10,
        null=True,
        blank=True,
        choices=[(rating.name, rating.value) for rating in SASS5Rating]
    )

    biotope_gravel = models.CharField(
        verbose_name='Biotope Gravel',
        help_text='Biotope Gravel',
        max_length=10,
        null=True,
        blank=True,
        choices=[(rating.name, rating.value) for rating in SASS5Rating]
    )

    biotope_sand = models.CharField(
        verbose_name='Biotope Sand',
        help_text='Biotope Sand',
        max_length=10,
        null=True,
        blank=True,
        choices=[(rating.name, rating.value) for rating in SASS5Rating]
    )

    biotope_mud = models.CharField(
        verbose_name='Biotope Mud',
        help_text='Biotope Mud',
        max_length=10,
        null=True,
        blank=True,
        choices=[(rating.name, rating.value) for rating in SASS5Rating]
    )

    biotope_hand_picking = models.CharField(
        verbose_name='Biotope Hand Picking',
        help_text='Biotope Hand Picking',
        max_length=10,
        null=True,
        blank=True,
        choices=[(rating.name, rating.value) for rating in SASS5Rating]
    )

    time_minutes = models.IntegerField(
        verbose_name='Time (min)',
        help_text='Time (min)',
        null=True,
        blank=True
    )

    notes = models.TextField(
        null=True,
        blank=True
    )

    other_biota = models.TextField(
        null=True,
        blank=True
    )

    sass_score = models.FloatField(
        null=True,
        blank=True
    )

    class Meta:
        """Meta class for project."""
        app_label = 'sass'
        verbose_name_plural = 'SASS 5 Sheets'
        verbose_name = 'SASS 5 Sheet'

    def __unicode__(self):
        return '{location_site} - {date}'.format(
            location_site=self.location_site.name,
            date=self.date
        )
