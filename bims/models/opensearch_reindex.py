from django.db import models
from django.utils import timezone


class OpenSearchReindexRun(models.Model):
    PENDING = 'pending'
    RUNNING = 'running'
    COMPLETED = 'completed'
    FAILED = 'failed'

    STATUS_CHOICES = (
        (PENDING, 'Pending'),
        (RUNNING, 'Running'),
        (COMPLETED, 'Completed'),
        (FAILED, 'Failed'),
    )

    status = models.CharField(
        max_length=16,
        choices=STATUS_CHOICES,
        default=PENDING,
    )
    recreate = models.BooleanField(default=False)
    chunk_size = models.PositiveIntegerField(default=500)
    requested_schema = models.CharField(max_length=63, blank=True, default='')
    total_tenants = models.PositiveIntegerField(default=0)
    completed_tenants = models.PositiveIntegerField(default=0)
    failed_tenants = models.PositiveIntegerField(default=0)
    started_at = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    error = models.TextField(blank=True, default='')

    class Meta:
        ordering = ('-started_at', '-id')

    def __str__(self):
        return f'OpenSearch reindex #{self.pk} ({self.status})'

    def finalize(self, status, error=''):
        self.status = status
        self.error = error
        self.finished_at = timezone.now()
        self.save(update_fields=['status', 'error', 'finished_at'])


class OpenSearchReindexTenantStatus(models.Model):
    PENDING = 'pending'
    RUNNING = 'running'
    COMPLETED = 'completed'
    FAILED = 'failed'

    STATUS_CHOICES = (
        (PENDING, 'Pending'),
        (RUNNING, 'Running'),
        (COMPLETED, 'Completed'),
        (FAILED, 'Failed'),
    )

    run = models.ForeignKey(
        'bims.OpenSearchReindexRun',
        related_name='tenant_statuses',
        on_delete=models.CASCADE,
    )
    schema_name = models.CharField(max_length=63)
    status = models.CharField(
        max_length=16,
        choices=STATUS_CHOICES,
        default=PENDING,
    )
    records_indexed = models.PositiveIntegerField(default=0)
    started_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    error = models.TextField(blank=True, default='')

    class Meta:
        ordering = ('schema_name',)
        unique_together = ('run', 'schema_name')

    def __str__(self):
        return f'{self.schema_name} ({self.status})'
