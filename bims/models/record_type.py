# coding=utf-8
"""Record type model definition.

"""
from django.db import models
from ordered_model.models import OrderedModel


class RecordType(OrderedModel):
    name = models.CharField(
        max_length=256,
    )

    is_hidden_in_form = models.BooleanField(
        help_text='Indicate if this record type'
                  ' should be hidden in forms.',
        default=False
    )

    def __str__(self):
        return self.name
