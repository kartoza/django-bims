# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2018-07-18 06:28
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bims', '0022_auto_20180718_0547'),
    ]

    operations = [
        migrations.AddField(
            model_name='shapefileuploadsession',
            name='token',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
    ]
