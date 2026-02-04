from django.db import models
from taggit.models import Tag


class TaxonTagDescription(models.Model):
    """Model to hold description for a Tag."""

    tag = models.OneToOneField(
        Tag,
        on_delete=models.CASCADE,
        related_name='description_detail'
    )
    description = models.TextField(
        blank=True,
        default=''
    )

    class Meta:
        verbose_name = "Tag Description"
        verbose_name_plural = "Tag Descriptions"

    def __str__(self):
        return f"Description for {self.tag.name}"
