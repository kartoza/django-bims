# coding=utf-8
"""Model for algae data, it has a reference to biological_collection_record

"""

from django.db import models


class DecisionSupportTool(models.Model):

    biological_collection_record = models.ForeignKey(
        'bims.BiologicalCollectionRecord',
        null=False,
        blank=False,
        on_delete=models.CASCADE
    )

    dst_name = models.ForeignKey(
        'bims.DecisionSupportToolName',
        null=True,
        blank=True,
        on_delete=models.SET_NULL
    )

    name = models.CharField(
        max_length=255,
        null=False,
        blank=False,
    )

    def __str__(self):
        try:
            return f'{self.name} - {self.biological_collection_record.uuid}'
        except Exception as e:
            return f'{self.name}'
