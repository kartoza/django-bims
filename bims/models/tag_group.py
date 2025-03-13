from colorfield.fields import ColorField
from django.db import models
from ordered_model.models import OrderedModelBase
from taggit.models import Tag


class TagGroup(OrderedModelBase):
    name = models.CharField(
        max_length=255, unique=True)
    colour = ColorField(default='#FF5733')
    order = models.PositiveIntegerField(
        default=0, help_text="Order of the tag group")
    tags = models.ManyToManyField(
        Tag, related_name='tag_groups')

    order_field_name = "order"

    class Meta:
        ordering = ("order",)

    def __str__(self):
        return self.name
