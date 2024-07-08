# coding=utf-8
"""Csv download model definition.

"""
from datetime import datetime

from django.contrib.sites.models import Site
from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from bims.tasks.email_csv import send_csv_via_email
from bims.download.csv_download import (
    send_rejection_csv
)


def validate_file_extension(value):
    import os
    ext = os.path.splitext(value.name)[1]
    valid_extensions = ['.csv', '.xlsx', '.xls']
    if ext not in valid_extensions:
        raise ValidationError('File not supported!')


class DownloadRequestPurpose(models.Model):
    name = models.CharField(
        max_length=512,
        blank=False,
        null=False
    )
    description = models.TextField(
        help_text='Optional',
        null=True,
        blank=True
    )
    order = models.IntegerField(
        null=False,
        blank=False
    )
    source_site = models.ForeignKey(
        Site,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    def __str__(self):
        return self.name

    class Meta:
        ordering = ('order',)


class DownloadRequest(models.Model):
    """Download request model
    """
    CSV = 'CSV'
    CHART = 'CHART'
    TABLE = 'TABLE'
    IMAGE = 'IMAGE'
    XLS = 'XLS'
    PDF = 'PDF'

    RESOURCE_TYPE_CHOICES = [
        (CSV, 'Csv'),
        (XLS, 'Xls'),
        (CHART, 'Chart'),
        (TABLE, 'Table'),
        (IMAGE, 'Image'),
        (PDF, 'Pdf'),
    ]

    requester = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        models.CASCADE,
        related_name='download_request_requester',
        blank=True,
        null=True,
    )
    request_date = models.DateTimeField(
        default=datetime.now
    )
    resource_type = models.CharField(
        max_length=10,
        choices=RESOURCE_TYPE_CHOICES,
        default=CSV
    )
    resource_name = models.CharField(
        max_length=256,
        default='',
        blank=True
    )
    taxon = models.ForeignKey(
        'bims.Taxonomy',
        null=True,
        blank=True,
        on_delete=models.SET_NULL
    )
    location_site = models.ForeignKey(
        'bims.LocationSite',
        null=True,
        blank=True,
        on_delete=models.SET_NULL
    )
    survey = models.ForeignKey(
        'bims.Survey',
        null=True,
        blank=True,
        on_delete=models.SET_NULL
    )
    purpose = models.ForeignKey(
        'bims.DownloadRequestPurpose',
        null=True,
        blank=True,
        on_delete=models.CASCADE
    )
    dashboard_url = models.TextField(
        null=True,
        blank=True
    )
    request_file = models.FileField(
        upload_to='request-files/',
        help_text='Only csv file',
        null=True,
        max_length=300,
        validators=[validate_file_extension]
    )
    notes = models.TextField(
        null=True,
        blank=True
    )
    processing = models.BooleanField(
        default=True
    )
    approved = models.BooleanField(
        default=False
    )
    request_category = models.CharField(
        max_length=256,
        default=''
    )
    rejected = models.BooleanField(
        default=False
    )
    rejection_message = models.TextField(
        null=True,
        blank=True
    )
    progress = models.CharField(
        max_length=255,
        null=True,
        blank=True
    )
    source_site = models.ForeignKey(
        Site,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    def get_formatted_name(self):
        """Return author formated full name, e.g. Maupetit J"""
        if not self.requester:
            return '-'
        if self.requester.first_name or self.requester.last_name:
            return '%s %s' % (
                self.requester.first_name, self.requester.last_name)
        return self.requester.username

    # noinspection PyClassicStyleClass
    class Meta:
        """Meta class for project."""
        app_label = 'bims'
        verbose_name_plural = 'Download requests'
        verbose_name = 'Download request'
        ordering = ('-request_date',)

    def __str__(self):
        return '{requester} - {date} - {category}'.format(
            requester=self.requester,
            date=self.request_date.strftime('%H:%M:%S'),
            category=self.request_category
        )

    def save(self, *args, **kwargs):
        old_obj = None

        if (
            not self.requester or
            self.resource_type != DownloadRequest.CSV or
            self.resource_type != DownloadRequest.XLS
        ):
            super(DownloadRequest, self).save(*args, **kwargs)
            return

        if self.id:
            old_obj = DownloadRequest.objects.get(id=self.id)

        if old_obj and not self.processing and not self.rejected:
            if self.approved and self.approved != old_obj.approved:
                # send email
                send_csv_via_email.delay(
                    self.requester.id,
                    self.request_file.path,
                    self.request_category,
                    approved=True
                )
        elif self.rejected and not self.approved and not self.processing:
            send_rejection_csv(
                self.requester,
                self.rejection_message
            )

        super(DownloadRequest, self).save(*args, **kwargs)
