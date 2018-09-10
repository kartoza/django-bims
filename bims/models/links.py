# coding: utf-8
__author__ = 'Alison Mukoma <alison@kartoza.com>'
__copyright__ = 'kartoza.com'

from django.db import models


class LinkCategory(models.Model):
    """Category model for a link."""

    name = models.CharField(max_length=50, unique=True)
    description = models.TextField(default='', blank=True)
    ordering = models.IntegerField(default=0)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ('ordering',)
        verbose_name_plural = 'categories'


class Link(models.Model):
    """Link model definition."""

    category = models.ForeignKey(LinkCategory, on_delete=models.CASCADE)
    name = models.CharField(max_length=50, unique=True)
    url = models.URLField(null=True, blank=True)
    description = models.TextField(default='', blank=True)
    ordering = models.IntegerField(default=0)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ('category__ordering', 'ordering',)
