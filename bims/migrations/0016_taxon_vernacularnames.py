# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2018-07-17 04:59
from __future__ import unicode_literals

import django.contrib.postgres.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bims', '0015_merge_20180706_0539'),
    ]

    operations = [
        migrations.AddField(
            model_name='taxon',
            name='vernacularNames',
            field=django.contrib.postgres.fields.ArrayField(base_field=models.CharField(blank=True, default=b'', max_length=100), default=[], size=None, verbose_name=b'Vernacular Names'),
        ),
    ]
