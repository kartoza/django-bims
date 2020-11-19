# coding=utf-8
"""Csv download model definition.

"""
from datetime import datetime
from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from bims.api_views.csv_download import (
    send_csv_via_email,
    send_rejection_csv,
    send_new_csv_notification
)


def validate_file_extension(value):
    import os
    ext = os.path.splitext(value.name)[1]
    valid_extensions = ['.csv']
    if ext not in valid_extensions:
        raise ValidationError('File not supported!')


class DownloadRequest(models.Model):
    """Csv document model
    """
    requester = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        models.CASCADE,
        related_name='download_request_requester',
        blank=False,
        null=False,
    )
    request_date = models.DateTimeField(
        default=datetime.now
    )
    request_file = models.FileField(
        upload_to='request-files/',
        help_text='Only csv file',
        null=True,
        max_length=300,
        validators=[validate_file_extension]
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

    def get_formatted_name(self):
        """Return author formated full name, e.g. Maupetit J"""
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

        if self._state.adding:
            send_new_csv_notification(
                self.requester,
                self.request_date
            )

        if self.id:
            old_obj = DownloadRequest.objects.get(id=self.id)

        if old_obj and not self.processing and not self.rejected:
            if self.approved and self.approved != old_obj.approved:
                # send email
                send_csv_via_email(
                    self.requester,
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
