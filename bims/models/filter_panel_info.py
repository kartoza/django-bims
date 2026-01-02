from django.db import models


class FilterPanelInfo(models.Model):
    """Stores descriptions for filter titles that appear in the map search panel."""

    title = models.CharField(
        max_length=255,
        unique=True,
        help_text='Matches the filter heading, e.g. "SPATIAL" or "TEMPORAL".'
    )
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Filter panel description'
        verbose_name_plural = 'Filter panel descriptions'
        ordering = ('title',)

    def __str__(self):
        return self.title

    @property
    def normalized_title(self):
        return (self.title or '').strip().upper()
