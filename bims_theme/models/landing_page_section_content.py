# coding=utf-8
"""Landing page section content model definition

"""
from django.db import models
from ordered_model.models import OrderedModel
from ckeditor_uploader.fields import RichTextUploadingField


class LandingPageSectionContent(OrderedModel):
    """Carousel header model."""
    name = models.CharField(
        max_length=255,
        null=False,
        blank=False,
        help_text='Name of the section, will not appear in the landing page'
    )

    content = RichTextUploadingField()

    def __str__(self):
        return self.name
