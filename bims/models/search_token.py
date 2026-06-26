import uuid
from django.db import models
from django.utils import timezone
from django.contrib.postgres.fields import ArrayField


class SearchToken(models.Model):
    """
    Stores the site_id list produced by an OpenSearch query so that Martin
    can retrieve it via a PostgreSQL function source and render vector tiles
    without needing a full materialized view.

    Tokens expire after TTL_HOURS and are cleaned up by a periodic task.
    """

    TTL_HOURS = 2

    token = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    schema_name = models.CharField(max_length=63)
    site_ids = ArrayField(
        base_field=models.IntegerField(),
        default=list,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    class Meta:
        indexes = [
            models.Index(fields=['expires_at']),
        ]

    def save(self, *args, **kwargs):
        if not self.expires_at:
            self.expires_at = timezone.now() + timezone.timedelta(
                hours=self.TTL_HOURS
            )
        super().save(*args, **kwargs)

    @property
    def is_expired(self):
        return timezone.now() >= self.expires_at

    @classmethod
    def cleanup_expired(cls):
        cls.objects.filter(expires_at__lt=timezone.now()).delete()
