# coding=utf-8
from django.conf import settings
from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType


class DataUpstreamDeletionCheckSession(models.Model):
    """Tracks one background run of the data upstream deletion check."""

    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('running', 'Running'),
        ('completed', 'Completed'),
        ('canceled', 'Canceled'),
        ('failed', 'Failed'),
    )
    SESSION_TYPES = (
        ('taxa', 'Taxa'),
        ('occurrences', 'Occurrence Records')
    )
    started_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='upstream_deletion_check_sessions',
    )
    taxon_group = models.ForeignKey(
        'bims.TaxonGroup',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    session_type = models.CharField(
        max_length=20,
        choices=SESSION_TYPES,
        default='taxa'
    )
    auto_remove = models.BooleanField(default=False)
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default='pending')
    total = models.IntegerField(default=0)
    processed = models.IntegerField(default=0)
    found_count = models.IntegerField(default=0)
    removed_count = models.IntegerField(default=0)
    canceled = models.BooleanField(default=False)
    error_message = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    last_progress_update = models.DateTimeField(null=True, blank=True)

    class Meta:
        app_label = 'bims'

    def __str__(self):
        return f'Data upstream deletion check #{self.pk} ({self.status})'


class DataUpstreamDeletionCheckResult(models.Model):
    """One row per data found to no longer exist on upstream."""

    session = models.ForeignKey(
        DataUpstreamDeletionCheckSession,
        on_delete=models.CASCADE,
        related_name='results',
    )
    object_id = models.CharField(
        max_length=255,
        verbose_name='Object ID',
    )
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        db_constraint=False,
    )
    content_object = GenericForeignKey('content_type', 'object_id')
    name = models.CharField(max_length=512, blank=True, default='')
    upstream_id = models.CharField(max_length=100, blank=True, default='')
    detail = models.TextField(blank=True, default='')
    removed = models.BooleanField(default=False)
    removed_at = models.DateTimeField(null=True, blank=True)
    removed_auto = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = 'bims'
        unique_together = ('session', 'object_id')

    def __str__(self):
        return f'{self.name} (id={self.upstream_id})'
