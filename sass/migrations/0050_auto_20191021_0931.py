# -*- coding: utf-8 -*-
# Generated by Django 1.11.23 on 2019-10-21 09:31
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('sass', '0049_auto_20191021_0925'),
    ]

    operations = [
        migrations.AlterField(
            model_name='sitevisitchem',
            name='chem',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='bims.Chem'),
        ),
    ]
