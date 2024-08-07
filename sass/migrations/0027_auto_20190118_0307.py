# -*- coding: utf-8 -*-
# Generated by Django 1.11.18 on 2019-01-18 03:07
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('bims', '0107_biologicalcollectionrecord_source_collection'),
        ('sass', '0026_sass5record'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='sass5record',
            name='family',
        ),
        migrations.AddField(
            model_name='sass5record',
            name='taxonomy',
            field=models.ForeignKey(blank=True, help_text=b'Family/Order Taxonomy', null=True, on_delete=django.db.models.deletion.SET_NULL, to='bims.Taxonomy', verbose_name=b'Family/Order Taxonomy'),
        ),
    ]
