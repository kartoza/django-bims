# -*- coding: utf-8 -*-
# Generated by Django 1.11.28 on 2020-04-30 04:00
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bims', '0237_auto_20200428_0551'),
    ]

    operations = [
        migrations.AddField(
            model_name='locationcontextgroup',
            name='verified',
            field=models.BooleanField(default=False),
        ),
    ]
