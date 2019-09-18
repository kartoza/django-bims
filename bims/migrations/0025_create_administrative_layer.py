# -*- coding: utf-8 -*-
from __future__ import unicode_literals

__author__ = 'Irwan Fathurrahman <irwan@kartoza.com>'
__date__ = '06/03/17'

from django.db import migrations, transaction
from django.db.utils import IntegrityError


def import_data(apps, schema_editor):
    db_alias = schema_editor.connection.alias
    NonBiodiversityLayer = apps.get_model("bims", "NonBiodiversityLayer")
    ibims_url = "http://lbimsgis.kartoza.com/geoserver/wms"
    layer_data = {
        "Administrative Provinces": "geonode:provinces_sa_2011",
        "Administrative Municipals": "geonode:district_council_sa_2011",
        "Administrative Districts": "geonode:district_municipalities_2011"
    }
    for layer_name, layer in layer_data.items():
        try:
            NonBiodiversityLayer.objects.create(
                name=layer_name,
                wms_url=ibims_url,
                wms_layer_name=layer
            )
        except IntegrityError:
            pass


class Migration(migrations.Migration):
    atomic = False
    dependencies = [
        ('bims', '0024_merge_20180719_0549'),
    ]

    operations = [
        migrations.RunPython(import_data),
    ]
