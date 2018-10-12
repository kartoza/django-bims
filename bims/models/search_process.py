# coding=utf-8
"""Search process model definition.

"""
from django.db import models


class SearchProcess(models.Model):
    """Search process model
    """
    SEARCH_TYPE = (
        ('cluster_generation', 'Cluster Generation'),
        ('search_results', 'Search Results'),
    )

    file_path = models.CharField(
        blank=True,
        max_length=250,
    )
    category = models.CharField(
        max_length=50,
        choices=SEARCH_TYPE,
        blank=False
    )
    query = models.CharField(
        max_length=2000,
        blank=False
    )
    process_id = models.CharField(
        max_length=200,
        blank=True
    )
    finished = models.BooleanField(
        default=False
    )
