# coding=utf-8
"""OGC layer model definition.

A saved BIMS filter that is served as an OGC API - Features collection,
so it can be added to GIS software as a live layer.
"""
import hashlib
import secrets
from datetime import timedelta

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

OGC_TOKEN_BYTES = 32
OGC_TOKEN_HINT_LENGTH = 6
# Do not write last_accessed more often than this
OGC_TOUCH_INTERVAL = timedelta(minutes=5)


def generate_ogc_token():
    return secrets.token_urlsafe(OGC_TOKEN_BYTES)


def hash_ogc_token(token):
    return hashlib.sha256(token.encode('utf-8')).hexdigest()


class OgcLayer(models.Model):
    """A saved filter published as an OGC API - Features layer.

    Only a hash of the layer token is stored. The plain token is available
    on ``raw_token`` right after the layer is created or the token is
    rotated, and cannot be recovered afterwards.
    """

    name = models.CharField(
        max_length=255
    )
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='ogc_layers'
    )
    token_hash = models.CharField(
        max_length=64,
        unique=True,
        editable=False,
        help_text='SHA-256 of the secret part of the layer URL.'
    )
    token_hint = models.CharField(
        max_length=OGC_TOKEN_HINT_LENGTH,
        editable=False,
        help_text='Last characters of the token, to tell layers apart.'
    )
    query = models.JSONField(
        default=dict,
        blank=True,
        help_text='Search filter parameters, as sent by the BIMS filter panel.'
    )
    include_sensitive = models.BooleanField(
        default=False,
        help_text='Include sensitive data, if the owner is allowed to see it.'
    )
    include_private = models.BooleanField(
        default=False,
        help_text='Include private data, if the owner is allowed to see it.'
    )
    is_active = models.BooleanField(
        default=True,
        help_text='Uncheck to revoke the layer URL.'
    )
    expires_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='The layer URL stops working after this date. '
                  'Leave empty for no expiry.'
    )
    created = models.DateTimeField(
        auto_now_add=True
    )
    last_accessed = models.DateTimeField(
        null=True,
        blank=True
    )
    record_count_cached = models.PositiveIntegerField(
        null=True,
        blank=True
    )
    record_count_updated = models.DateTimeField(
        null=True,
        blank=True
    )

    raw_token = None

    class Meta:
        ordering = ('-created',)

    def __str__(self):
        return self.name

    @property
    def is_expired(self):
        return bool(self.expires_at and self.expires_at <= timezone.now())

    @property
    def is_available(self):
        """Whether the layer URL can currently be served."""
        return self.is_active and not self.is_expired

    @classmethod
    def get_by_token(cls, token):
        """Return the layer for a plain token, or None if there is none."""
        if not token:
            return None
        return cls.objects.filter(token_hash=hash_ogc_token(token)).first()

    def _set_token(self, token):
        self.raw_token = token
        self.token_hash = hash_ogc_token(token)
        self.token_hint = token[-OGC_TOKEN_HINT_LENGTH:]

    def rotate_token(self):
        """Replace the token, which invalidates the previous URL.

        :return: the new plain token. It is not stored anywhere.
        """
        self._set_token(generate_ogc_token())
        self.save(update_fields=['token_hash', 'token_hint'])
        return self.raw_token

    def touch(self, now=None):
        """Record an access, at most once per OGC_TOUCH_INTERVAL.

        :return: True if last_accessed was written.
        """
        now = now or timezone.now()
        stale_before = now - OGC_TOUCH_INTERVAL
        updated = OgcLayer.objects.filter(pk=self.pk).filter(
            models.Q(last_accessed__isnull=True) |
            models.Q(last_accessed__lt=stale_before)
        ).update(last_accessed=now)
        if updated:
            self.last_accessed = now
        return bool(updated)

    def clean(self):
        super().clean()
        errors = {}
        if not isinstance(self.query, dict):
            errors['query'] = 'The query must be a JSON object.'
        owner = getattr(self, 'owner', None) if self.owner_id else None
        if owner is not None:
            group_names = set(owner.groups.values_list('name', flat=True))
            if (
                self.include_sensitive and
                'SensitiveDataGroup' not in group_names
            ):
                errors['include_sensitive'] = (
                    'The owner is not allowed to access sensitive data.'
                )
            if (
                self.include_private and
                'PrivateDataGroup' not in group_names
            ):
                errors['include_private'] = (
                    'The owner is not allowed to access private data.'
                )
        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        if not self.token_hash:
            self._set_token(generate_ogc_token())
        super().save(*args, **kwargs)
