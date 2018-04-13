# coding=utf-8
"""Location context model definition.

"""
from django.db import models


class LocationContext(models.Model):

    context_document = models.TextField()
