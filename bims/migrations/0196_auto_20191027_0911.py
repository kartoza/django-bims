# -*- coding: utf-8 -*-
# Generated by Django 1.11.23 on 2019-10-27 09:11
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('bims', '0195_auto_20191021_0931'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='chem',
            options={'verbose_name': 'Chemistry unit', 'verbose_name_plural': 'Chemistry units'},
        ),
    ]
