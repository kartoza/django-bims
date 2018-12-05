# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


def move_taxon_value(apps, schema_editor):
    BioCollectionRecords = apps.get_model('bims', 'BiologicalCollectionRecord')
    Taxonomy = apps.get_model('bims', 'Taxonomy')
    collections = BioCollectionRecords.objects.filter(
        taxonomy__isnull=True,
        taxon_gbif_id__isnull=False
    )
    for collection in collections:
        print('Move taxonomy value for %s - %s' % (collection.original_species_name, collection.pk))
        if not collection.taxon_gbif_id:
            continue

        if not collection.taxon_gbif_id.gbif_id:
            continue

        if collection.pk == 20244:
            print('something')

        taxonomy = Taxonomy.objects.get(
            gbif_key=collection.taxon_gbif_id.gbif_id
        )
        collection.taxonomy = taxonomy
        collection.taxon_gbif_id = None
        collection.save()


class Migration(migrations.Migration):

    dependencies = [
        ('bims', '0081_migrate_old_taxon'),
    ]

    operations = [
        migrations.RunPython(move_taxon_value),
    ]
