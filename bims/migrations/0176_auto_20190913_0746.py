# -*- coding: utf-8 -*-
# Generated by Django 1.11.23 on 2019-09-13 07:46
from __future__ import unicode_literals

import django.contrib.postgres.fields.jsonb
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('bims', '0175_chemicalrecord'),
    ]

    operations = [
        migrations.AddField(
            model_name='chemicalrecord',
            name='additional_data',
            field=django.contrib.postgres.fields.jsonb.JSONField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='chemicalrecord',
            name='source_reference',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='bims.SourceReference'),
        ),
    ]
