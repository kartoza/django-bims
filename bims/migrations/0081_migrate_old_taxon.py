# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from bims.utils.gbif import process_taxon_identifier
from django.db import migrations, models


def move_taxon_value(apps, schema_editor):
    Taxon = apps.get_model('bims', 'Taxon')
    IUCNStatus = apps.get_model('bims', 'IUCNStatus')
    Taxonomy = apps.get_model('bims', 'Taxonomy')
    taxa = Taxon.objects.all()
    for taxon in taxa:
        if Taxonomy.objects.filter(gbif_key=taxon.gbif_id).exists():
            continue
        print('Migrate %s' % taxon.scientific_name)
        taxon_identifier = process_taxon_identifier(taxon.gbif_id)
        if taxon_identifier:
            taxon_identifier.iucn_data = taxon.iucn_data
            taxon_identifier.iucn_redlist_id = taxon.iucn_redlist_id
            taxon_identifier.save()
            if taxon.iucn_status:
                iucn_status = IUCNStatus.objects.get(pk=taxon.iucn_status.pk)
                taxonomy = Taxonomy.objects.get(id=taxon_identifier.id)
                taxonomy.iucn_status = iucn_status
                taxonomy.save()


class Migration(migrations.Migration):

    dependencies = [
        ('bims', '0080_biologicalcollectionrecord_taxonomy'),
    ]

    operations = [
        migrations.RunPython(move_taxon_value),
    ]
