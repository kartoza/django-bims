# -*- coding: utf-8 -*-
# Generated by Django 1.11.18 on 2019-02-26 06:46
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bims', '0116_auto_20190226_0630'),
    ]

    operations = [
        migrations.AddField(
            model_name='spatialscale',
            name='key',
            field=models.CharField(blank=True, max_length=200, null=True),
        ),
        migrations.AddField(
            model_name='spatialscalegroup',
            name='key',
            field=models.CharField(blank=True, max_length=200, null=True),
        ),
    ]
