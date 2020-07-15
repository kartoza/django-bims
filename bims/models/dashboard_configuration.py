# coding=utf-8
"""Dashboard configuration session model definition.

"""
from datetime import datetime
from django.db import models
from django.contrib.postgres.fields import JSONField
from bims.models.taxon_group import TaxonGroup


class DashboardConfiguration(models.Model):
    """Dashboard configuration model
    """
    module_group = models.OneToOneField(
        TaxonGroup,
        null=False,
        blank=False,
        on_delete=models.CASCADE
    )

    modified = models.DateTimeField(
        default=datetime.now
    )

    additional_data = JSONField(
        blank=True,
        null=True
    )

    # noinspection PyClassicStyleClass
    class Meta:
        """Meta class for project."""
        app_label = 'bims'
        verbose_name_plural = 'Dashboard Configurations'
        verbose_name = 'Dashboard Configuration'

    def __str__(self):
        return self.module_group.name
