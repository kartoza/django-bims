# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2018-07-18 05:47
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bims', '0021_shapefileuploadsession_token'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='shapefileuploadsession',
            name='token',
        ),
        migrations.AddField(
            model_name='shapefile',
            name='token',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
    ]
