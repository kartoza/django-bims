# coding=utf-8
"""Landing page section content model definition

"""

from django.db import models
from ordered_model.models import OrderedModel
from ckeditor.fields import RichTextField


class LandingPageSectionContent(OrderedModel):
    """Carousel header model."""
    name = models.CharField(
        max_length=255,
        null=False,
        blank=False,
        help_text='Name of the section, will not appear in the landing page'
    )
    content = RichTextField()

    def __str__(self):
        return self.name
