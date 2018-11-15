# coding=utf-8
"""Reference link model definition.
"""

from django.contrib.gis.db import models
from bims.models import BiologicalCollectionRecord
from td_biblio.models import Entry


class ReferenceLink(models.Model):

    collection_record = models.ForeignKey(
        BiologicalCollectionRecord,
        on_delete=models.CASCADE
    )

    reference = models.ForeignKey(
        Entry,
        on_delete=models.CASCADE
    )
