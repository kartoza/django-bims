# coding=utf-8
"""Hydroperiod Status model definition.

"""
from django.db import models
from ordered_model.models import OrderedModel


class Hydroperiod(OrderedModel):
    name = models.CharField(
        max_length=256,
    )

    def __str__(self):
        return self.name
