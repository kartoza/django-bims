# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from bims.utils.gbif import process_taxon_identifier
from django.db import migrations, models


def move_taxon_value(apps, schema_editor):
    Taxon = apps.get_model('bims', 'Taxon')
    Taxonomy = apps.get_model('bims', 'Taxonomy')
    taxa = Taxon.objects.all()
    for taxon in taxa:
        if not Taxonomy.objects.filter(gbif_key=taxon.gbif_id).exists():
            continue
        taxon_identifier = Taxonomy.objects.get(gbif_key=taxon.gbif_id)
        taxon_identifier.author = taxon.author
        taxon_identifier.save()


class Migration(migrations.Migration):

    dependencies = [
        ('bims', '0087_taxonomy_author'),
    ]

    operations = [
        migrations.RunPython(move_taxon_value),
    ]
