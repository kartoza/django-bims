# coding=utf-8
"""Wetland Indicator Status model definition.

"""
from django.db import models
from ordered_model.models import OrderedModel


class WetlandIndicatorStatus(OrderedModel):
    name = models.CharField(
        max_length=256,
    )

    def __str__(self):
        return self.name
