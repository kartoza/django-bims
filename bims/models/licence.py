# coding=utf-8
"""Licence model definition.

"""
from django.db import models


class Licence(models.Model):
    name = models.CharField(max_length=100)
    identifier = models.CharField(max_length=50)
    description = models.TextField(blank=True)
    url = models.URLField(blank=True)

    def __str__(self):
        return self.identifier
