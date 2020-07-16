# coding=utf-8
"""Harvest session model definition.

"""
import uuid
from django.conf import settings
from datetime import datetime
from django.db import models
from bims.models.taxon_group import TaxonGroup


class HarvestSession(models.Model):
    """Harvest session model
    """
    CATEGORY_CHOICES = (
        ('gbif', 'GBIF'),
    )

    harvester = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        models.SET_NULL,
        related_name='harvest_session_harvester',
        blank=True,
        null=True,
    )

    module_group = models.ForeignKey(
        TaxonGroup,
        null=True,
        blank=True,
        on_delete=models.CASCADE
    )

    start_time = models.DateTimeField(
        default=datetime.now
    )

    category = models.CharField(
        max_length=50,
        choices=CATEGORY_CHOICES,
        blank=True,
        default='',
    )

    finished = models.BooleanField(
        default=False
    )

    log_file = models.FileField(
        upload_to='harvest-session-log/',
        null=True
    )

    status = models.TextField(
        null=True,
        blank=True
    )

    def __str__(self):
        return '{start} - {finished}'.format(
            start=self.start_time,
            finished=self.finished
        )
