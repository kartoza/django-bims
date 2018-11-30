# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


def move_endemism_value(apps, schema_editor):
    BioCollectionRecords = apps.get_model('bims', 'BiologicalCollectionRecord')
    Endemism = apps.get_model('bims', 'Endemism')
    collections = BioCollectionRecords.objects.filter(
        endemism__isnull=False
    ).exclude(
        endemism__exact=''
    )
    for collection in collections:
        endemism, status = Endemism.objects.get_or_create(
            name=collection.endemism
        )
        taxon_gbif = collection.taxon_gbif_id
        if taxon_gbif:
            taxon_gbif.endemism = endemism
            taxon_gbif.save()


class Migration(migrations.Migration):

    dependencies = [
        ('bims', '0068_taxon_endemism'),
    ]

    operations = [
        migrations.RunPython(move_endemism_value),
    ]
