# coding=utf-8
"""Request log definition.

"""

from django.db import models
from django.conf import settings


class RequestLog(models.Model):

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        models.SET_NULL,
        blank=True,
        null=True,
    )

    remote_address = models.CharField(
        max_length=100,
        null=True,
        blank=True
    )

    server_hostname = models.CharField(
        max_length=100,
        null=True,
        blank=True
    )

    request_path = models.CharField(
        max_length=255,
        null=True,
        blank=True
    )

    response_status = models.IntegerField(
        null=True,
        blank=True
    )

    start_time = models.FloatField(
        null=True,
        blank=True
    )

    run_time = models.FloatField(
        null=True,
        blank=True
    )
