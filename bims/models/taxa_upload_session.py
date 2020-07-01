# coding=utf-8
"""Taxa upload session model definition.

"""
import uuid
from django.conf import settings
from datetime import datetime
from django.db import models
from bims.models.taxon_group import TaxonGroup


class TaxaUploadSession(models.Model):
    """Taxa upload session model
    """
    uploader = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        models.SET_NULL,
        blank=True,
        null=True,
    )

    module_group = models.ForeignKey(
        TaxonGroup,
        null=True,
        blank=True,
        on_delete=models.CASCADE
    )

    token = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        null=True
    )

    uploaded_at = models.DateTimeField(
        default=datetime.now
    )

    processed = models.BooleanField(
        default=False
    )

    error_notes = models.TextField(
        blank=True,
        null=True
    )

    progress = models.CharField(
        max_length=200,
        default='',
        blank=True
    )

    process_file = models.FileField(
        upload_to='taxa-file/',
        null=True
    )

    success_file = models.FileField(
        upload_to='taxa-file/',
        null=True,
        blank=True
    )

    error_file = models.FileField(
        upload_to='taxa-file/',
        null=True,
        blank=True
    )

    updated_file = models.FileField(
        upload_to='taxa-file/',
        null=True,
        blank=True
    )

    # noinspection PyClassicStyleClass
    class Meta:
        """Meta class for project."""
        app_label = 'bims'
        verbose_name_plural = 'Taxa Upload Sessions'
        verbose_name = 'Taxa Upload Session'

    def __str__(self):
        return str(self.token)
